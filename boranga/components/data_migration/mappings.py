from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Literal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from boranga.components.main.models import LegacyValueMap
from boranga.components.species_and_communities.models import GroupType

logger = logging.getLogger(__name__)

# sentinel string used to mark intentional ignores (default: "__IGNORE__")
IGNORE_SENTINEL = getattr(settings, "LEGACY_IGNORE_SENTINEL", "__IGNORE__")

# Cache: (legacy_system, list_name) -> dict[norm_legacy_value] = mapping dict
_CACHE: dict[tuple[str, str], dict[str, dict]] = {}


def _norm(s: Any) -> str:
    return str(s).strip().casefold()


def preload_map(legacy_system: str, list_name: str, active_only: bool = True):
    key = (legacy_system, list_name)
    if key in _CACHE:
        return
    qs = LegacyValueMap.objects.filter(
        legacy_system=legacy_system,
        list_name=list_name,
    )
    if active_only:
        qs = qs.filter(active=True)
    data: dict[str, dict] = {}
    for row in qs.select_related("target_content_type"):
        # Preserve intentional ignore sentinel entries in the map so callers
        # can detect and silently ignore them.
        canon = (row.canonical_name or "").strip()
        key = _norm(row.legacy_value)
        if canon.casefold() == IGNORE_SENTINEL.casefold():
            data[key] = {
                "target_id": None,
                "content_type_id": None,
                "canonical": None,
                "raw": row.legacy_value,
                "ignored": True,
            }
        else:
            data[key] = {
                "target_id": row.target_object_id,
                "content_type_id": row.target_content_type_id,
                "canonical": row.canonical_name,
                "raw": row.legacy_value,
                "ignored": False,
            }
    _CACHE[key] = data


ReturnMode = Literal["id", "canonical", "both"]


def load_species_to_district_links(
    legacy_system: str,
    path: str | None = None,
    key_column: str = "TXN_LST_ID",
    district_column: str = "DST_ID",
    delimiter: str = ";",
) -> dict[str, list[str]]:
    """
    Build a mapping: migrated_from_id -> list of legacy district keys.

    This version assumes a CSV source (path or settings.LEGACY_SPECIES_DISTRICTS_PATH)
    and does not attempt any model-based fallback.
    """
    mapping: dict[str, list[str]] = {}

    # directory containing the current file
    BASE_DIR = Path(__file__).resolve().parent

    # default import file path
    default_csv_path = BASE_DIR / "legacy_data/TPFL/DRF_TAXON_CONSV_LST_DISTRICTS.csv"

    csv_path = (
        path
        or default_csv_path
        or getattr(settings, "LEGACY_SPECIES_DISTRICTS_PATH", None)
    )

    if not csv_path:
        logger.warning(
            "No CSV path provided for species->district links (legacy_system=%s)",
            legacy_system,
        )
        return mapping

    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if (
                not reader.fieldnames
                or key_column not in reader.fieldnames
                or district_column not in reader.fieldnames
            ):
                logger.warning(
                    "CSV %s missing expected columns (%s, %s); found: %s",
                    csv_path,
                    key_column,
                    district_column,
                    reader.fieldnames,
                )
                return mapping
            for row in reader:
                key = (row.get(key_column) or "").strip()
                if not key:
                    continue
                raw = (row.get(district_column) or "").strip()
                if not raw:
                    continue
                if delimiter and delimiter in raw:
                    parts = [p.strip() for p in raw.split(delimiter) if p.strip()]
                else:
                    parts = [raw] if raw else []
                if parts:
                    mapping.setdefault(key, []).extend(parts)
        return mapping
    except FileNotFoundError:
        logger.warning("Species->district CSV path not found: %s", csv_path)
        return mapping
    except Exception as exc:
        logger.exception("Error reading species->district CSV %s: %s", csv_path, exc)
        return mapping


def load_legacy_to_pk_map(
    legacy_system: str,
    model_name: str,
    app_label: str = "boranga",
) -> dict[str, int]:
    """
    Return a mapping of legacy_value -> target model PK for entries registered
    in LegacyValueMap for the given legacy_system and model.

    Strategy:
    - Prefer LegacyValueMap rows whose target_content_type matches the requested model.
    - Fallback to LegacyValueMap rows where list_name == model_name (if any).
    - Only active=True entries are considered.
    """
    mapping: dict[str, int] = {}

    # resolve content type for the target model if possible
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_name.lower())
    except ContentType.DoesNotExist:
        ct = None

    qs = LegacyValueMap.objects.filter(legacy_system__iexact=legacy_system, active=True)
    if ct is not None:
        qs = qs.filter(target_content_type=ct)
    else:
        qs = qs.filter(list_name__iexact=model_name)

    for row in qs.select_related("target_content_type"):
        canon = (row.canonical_name or "").strip()
        key = str(row.legacy_value).strip()
        if not key:
            continue
        # record intentional ignore as an explicit None value so callers can
        # distinguish "ignored" vs "missing"
        if canon.casefold() == IGNORE_SENTINEL.casefold():
            mapping[key] = None
            continue
        if row.target_object_id:
            # later entries may override earlier; keep last-seen
            mapping[key] = int(row.target_object_id)

    logger.debug(
        "load_legacy_to_pk_map: loaded %d mappings for %s -> %s",
        len(mapping),
        legacy_system,
        model_name,
    )
    return mapping


def load_csv_mapping(
    csv_filename: str,
    key_column: str,
    value_column: str,
    legacy_system: str | None = None,
    path: str | None = None,
    *,
    delimiter: str = ",",
    case_insensitive: bool = True,
) -> tuple[dict[str, str] | None, str]:
    """
    Load a simple CSV mapping file (headers include key_column and value_column).

    Parameters:
      - csv_filename: name of the CSV file (e.g. "DRF_LOV_RECORD_SOURCE_VWS.csv").
      - key_column / value_column: header names in the CSV to use for mapping.
      - legacy_system: optional legacy system subfolder to look under the default
        legacy_data directory (e.g. "TPFL"). Ignored when `path` is provided.
      - path: optional directory or full path to the CSV file. If omitted the
        default directory is "<data_migration>/legacy_data" (next to this file).
        If `path` is a directory the csv_filename will be joined to it. If it
        already points to a .csv file it will be used as-is.
      - delimiter, case_insensitive: parsing options.

    Returns (mapping_dict, resolved_path) or (None, resolved_path) if file not found
    or could not be read.
    """
    base_dir = Path(__file__).resolve().parent

    # Resolve file path:
    if path:
        p = Path(path)
        if p.suffix and p.suffix.lower() == ".csv":
            resolved = p
        else:
            # treat provided path as directory
            resolved = p / csv_filename
    else:
        # include legacy_system as a subdirectory under legacy_data when provided
        if legacy_system:
            resolved = base_dir / "legacy_data" / legacy_system / csv_filename
        else:
            resolved = base_dir / "legacy_data" / csv_filename

    resolved_str = str(resolved)

    mapping: dict[str, str] = {}
    try:
        with open(resolved_str, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh, delimiter=delimiter)
            if (
                not rdr.fieldnames
                or key_column not in rdr.fieldnames
                or value_column not in rdr.fieldnames
            ):
                logger.warning(
                    "CSV %s missing expected columns (%s, %s); found: %s",
                    resolved_str,
                    key_column,
                    value_column,
                    rdr.fieldnames,
                )
                return None, resolved_str
            for row in rdr:
                k = row.get(key_column)
                v = row.get(value_column)
                if k is None:
                    continue
                key_norm = str(k).strip()
                if case_insensitive:
                    key_norm = key_norm.casefold()
                mapping[key_norm] = v
        return mapping, resolved_str
    except FileNotFoundError:
        logger.debug("CSV mapping file not found: %s", resolved_str)
        return None, resolved_str
    except Exception as exc:
        logger.exception("Error reading CSV mapping %s: %s", resolved_str, exc)
        return None, resolved_str


# simple in-process cache for GroupType id lookups
_GROUP_TYPE_CACHE: dict[str, int] = {}


def get_group_type_id(name: str) -> int | None:
    """
    Return GroupType.id for the given name (case-insensitive). Cached in-process.
    Returns None if no matching GroupType is found.
    """
    if not name:
        return None
    key = str(name).strip().casefold()
    if key in _GROUP_TYPE_CACHE:
        return _GROUP_TYPE_CACHE[key]
    try:
        obj = GroupType.objects.filter(name__iexact=name).first()
        if obj:
            _GROUP_TYPE_CACHE[key] = obj.id
            return obj.id
    except Exception:
        logger.exception("Error looking up GroupType %s", name)
    return None
