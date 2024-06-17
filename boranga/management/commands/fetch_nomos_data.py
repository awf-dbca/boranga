import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from boranga.components.species_and_communities.models import (
    ClassificationSystem,
    CrossReference,
    InformalGroup,
    Kingdom,
    Taxonomy,
    TaxonomyRank,
    TaxonVernacular,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch nomos data"

    def handle(self, *args, **options):
        logger.info(f"Running command {__name__}")

        errors = []
        updates = []

        my_url = f"{settings.NOMOS_URL}/token"

        username = settings.NOMOS_USERNAME
        passwd = settings.NOMOS_PASSWORD

        data1 = [
            {
                "grant_type": "password",
                "scope": "READER",
                "username": username,
                "password": passwd,
            }
        ]

        try:
            res = requests.post(my_url, data=data1[0])
            if res.status_code == 200:
                r = res.json()
                r["access_token"]
                token = "{} {}".format(r["token_type"], r["access_token"])
                logger.info(f"Access token {token}")

                taxon_url = f"{settings.NOMOS_URL}/v1/taxon_names?range=[0,500]"
                taxon_res = requests.get(taxon_url, headers={"Authorization": token})
                tres = taxon_res.json()
                try:
                    for t in tres:
                        author = t["author"] if "author" in t else ""
                        notes = t["notes"] if "notes" in t else ""

                        # kingdom
                        kingdom_fk = Kingdom.objects.get(kingdom_id=t["kingdom_id"])

                        # Taxon rank from the hierarchy
                        taxon_rank_id = t["rank_id"]
                        taxon_rank_fk = TaxonomyRank.objects.get(
                            taxon_rank_id=taxon_rank_id
                        )

                        # Taxon's family_nid(taxon_name_id) ref from the rank hierarchy
                        family_nid = t["family_nid"] if "family_nid" in t else None
                        family_fk = None
                        # to check if family exists else retrieve it from other api taxon_names/{taxon_name_id}
                        if family_nid:
                            try:
                                family_fk = Taxonomy.objects.get(
                                    taxon_name_id=family_nid
                                )

                            except Taxonomy.DoesNotExist:
                                #  create taxon for the family_nid(taxon_name_id) in the hierarchy
                                family_url = "{}/v1/taxon_names/{}".format(
                                    settings.NOMOS_URL, family_nid
                                )
                                family_res = requests.get(
                                    family_url, headers={"Authorization": token}
                                )
                                fres = family_res.json()
                                try:
                                    family_author = (
                                        fres["author"] if "author" in fres else ""
                                    )
                                    family_notes = (
                                        fres["notes"] if "notes" in fres else ""
                                    )

                                    # kingdom
                                    family_kingdom_fk = Kingdom.objects.get(
                                        kingdom_id=fres["kingdom_id"]
                                    )

                                    # Taxon rank from the hierarchy
                                    family_taxon_rank_id = fres["rank_id"]
                                    family_taxon_rank_fk = TaxonomyRank.objects.get(
                                        taxon_rank_id=family_taxon_rank_id
                                    )

                                    family_obj, created = (
                                        Taxonomy.objects.update_or_create(
                                            taxon_name_id=fres["taxon_name_id"],
                                            defaults={
                                                "scientific_name": fres[
                                                    "canonical_name"
                                                ],
                                                "kingdom_id": fres["kingdom_id"],
                                                "kingdom_fk": family_kingdom_fk,
                                                "kingdom_name": fres["kingdom"][
                                                    "kingdom_name"
                                                ],
                                                "name_authority": family_author,
                                                "name_comments": family_notes,
                                                "name_currency": fres["is_current"],
                                                "taxon_rank_id": family_taxon_rank_id,
                                                "taxonomy_rank_fk": family_taxon_rank_fk,
                                                "path": fres["path"],
                                            },
                                        )
                                    )
                                    family_fk = family_obj
                                except Exception as e:
                                    err_msg = "Create family taxon:"
                                    logger.error(f"{err_msg}\n{str(e)}")
                                    errors.append(err_msg)

                        taxon_obj, created = Taxonomy.objects.update_or_create(
                            taxon_name_id=t["taxon_name_id"],
                            defaults={
                                "scientific_name": t["canonical_name"],
                                "kingdom_id": t["kingdom_id"],
                                "kingdom_fk": kingdom_fk,
                                "kingdom_name": t["kingdom"]["kingdom_name"],
                                "name_authority": author,
                                "name_comments": notes,
                                "name_currency": t["is_current"],
                                "taxon_rank_id": taxon_rank_id,
                                "taxonomy_rank_fk": taxon_rank_fk,
                                "family_nid": family_nid,
                                "family_fk": family_fk,
                                "path": t["path"],
                            },
                        )
                        # logger.info('Taxon {}'.format(obj.scientific_name))
                        updates.append(taxon_obj.id)

                        # check if tha taxon has classification_systems_ids and then create the informal group
                        # records for taxon which will be the "phylo group for a taxon"
                        if taxon_obj:
                            if t["classification_system_ids"]:
                                informal_grp_url = (
                                    "{}/v1/informal_groups?filter={}{}{}".format(
                                        settings.NOMOS_URL,
                                        '{"taxon_name_id":',
                                        taxon_obj.taxon_name_id,
                                        "}",
                                    )
                                )
                                informal_grp_res = requests.get(
                                    informal_grp_url, headers={"Authorization": token}
                                )
                                gres = informal_grp_res.json()
                                try:
                                    # A taxon can have more than one informal groups
                                    for g in gres:
                                        # classification system id
                                        classification_system_id = g[
                                            "classification_system_id"
                                        ]
                                        classification_system_fk = ClassificationSystem.objects.get(
                                            classification_system_id=classification_system_id
                                        )

                                        obj, created = (
                                            InformalGroup.objects.update_or_create(
                                                informal_group_id=g[
                                                    "informal_group_id"
                                                ],
                                                defaults={
                                                    "classification_system_id": classification_system_id,
                                                    "classification_system_fk": classification_system_fk,
                                                    "taxon_name_id": g["taxon_name_id"],
                                                    "taxonomy": taxon_obj,
                                                },
                                            )
                                        )
                                except Exception as e:
                                    err_msg = "Create informal group:"
                                    logger.error(f"{err_msg}\n{str(e)}")
                                    errors.append(err_msg)

                        # check if the taxon has all_vernaculars and then create the TaxonVernacular
                        # records for taxon which will be the "common names"
                        if taxon_obj:
                            all_vernaculars = (
                                t["all_vernaculars"] if "all_vernaculars" in t else ""
                            )
                            if all_vernaculars != "":
                                vern_url = "{}/v1/vernaculars?filter={}{}{}".format(
                                    settings.NOMOS_URL,
                                    '{"taxon_name_id":',
                                    taxon_obj.taxon_name_id,
                                    "}",
                                )
                                vern_res = requests.get(
                                    vern_url, headers={"Authorization": token}
                                )
                                vres = vern_res.json()
                                try:
                                    # A taxon can have more than one vernaculars(common names)
                                    for v in vres:
                                        obj, created = (
                                            TaxonVernacular.objects.update_or_create(
                                                vernacular_id=v["vernacular_id"],
                                                defaults={
                                                    "vernacular_name": v[
                                                        "vernacular_name"
                                                    ],
                                                    "taxonomy": taxon_obj,
                                                    "taxon_name_id": taxon_obj.taxon_name_id,
                                                },
                                            )
                                        )

                                except Exception as e:
                                    err_msg = "Create Taxon Vernacular:"
                                    logger.error(f"{err_msg}\n{str(e)}")
                                    errors.append(err_msg)

                        # check if the taxon has previous name in cross_reference table as
                        # in new_name_id field and then get the old_name_id
                        if taxon_obj:
                            x_ref_url = "{}/v1/cross_references?filter={}{}{}".format(
                                settings.NOMOS_URL,
                                '{"new_name_id":',
                                taxon_obj.taxon_name_id,
                                "}",
                            )
                            x_ref_res = requests.get(
                                x_ref_url, headers={"Authorization": token}
                            )
                            xres = x_ref_res.json()
                            try:
                                # A taxon can have more than one previous names
                                for x in xres:
                                    old_name_id = (
                                        x["old_name_id"] if "old_name_id" in x else None
                                    )
                                    old_taxon_fk = None
                                    if old_name_id:
                                        try:
                                            old_taxon_fk = Taxonomy.objects.get(
                                                taxon_name_id=old_name_id
                                            )

                                        except Taxonomy.DoesNotExist:
                                            #  create taxon for the old(taxon_name_id) in the hierarchy
                                            old_taxon_url = (
                                                "{}/v1/taxon_names/{}".format(
                                                    settings.NOMOS_URL, old_name_id
                                                )
                                            )
                                            old_taxon_res = requests.get(
                                                old_taxon_url,
                                                headers={"Authorization": token},
                                            )
                                            ores = old_taxon_res.json()
                                            try:
                                                old_taxon_author = (
                                                    ores["author"]
                                                    if "author" in ores
                                                    else ""
                                                )
                                                old_taxon_notes = (
                                                    ores["notes"]
                                                    if "notes" in ores
                                                    else ""
                                                )

                                                # kingdom
                                                old_taxon_kingdom_fk = (
                                                    Kingdom.objects.get(
                                                        kingdom_id=ores["kingdom_id"]
                                                    )
                                                )

                                                # Taxon rank from the hierarchy
                                                old_taxon_rank_id = ores["rank_id"]
                                                old_taxon_rank_fk = (
                                                    TaxonomyRank.objects.get(
                                                        taxon_rank_id=old_taxon_rank_id
                                                    )
                                                )

                                                old_taxon_obj, created = (
                                                    Taxonomy.objects.update_or_create(
                                                        taxon_name_id=ores[
                                                            "taxon_name_id"
                                                        ],
                                                        defaults={
                                                            "scientific_name": ores[
                                                                "canonical_name"
                                                            ],
                                                            "kingdom_id": ores[
                                                                "kingdom_id"
                                                            ],
                                                            "kingdom_fk": old_taxon_kingdom_fk,
                                                            "kingdom_name": ores[
                                                                "kingdom"
                                                            ]["kingdom_name"],
                                                            "name_authority": old_taxon_author,
                                                            "name_comments": old_taxon_notes,
                                                            "name_currency": ores[
                                                                "is_current"
                                                            ],
                                                            "taxon_rank_id": old_taxon_rank_id,
                                                            "taxonomy_rank_fk": old_taxon_rank_fk,
                                                            "path": ores["path"],
                                                        },
                                                    )
                                                )
                                                old_taxon_fk = old_taxon_obj
                                            except Exception as e:
                                                err_msg = "Create Old Name(Previous Name) taxon:"
                                                logger.error(f"{err_msg}\n{str(e)}")
                                                errors.append(err_msg)

                                    x_ref_obj, created = (
                                        CrossReference.objects.update_or_create(
                                            cross_reference_id=x["cross_reference_id"],
                                            defaults={
                                                "cross_reference_type": x[
                                                    "cross_reference_type"
                                                ],
                                                "old_name_id": old_name_id,
                                                "new_name_id": taxon_obj.taxon_name_id,
                                                "old_taxonomy": old_taxon_fk,
                                                "new_taxonomy": taxon_obj,
                                            },
                                        )
                                    )

                            except Exception as e:
                                err_msg = "Create Taxon Cross Reference:"
                                logger.error(f"{err_msg}\n{str(e)}")
                                errors.append(err_msg)

                except Exception as e:
                    err_msg = "Create taxon:"
                    logger.error(f"{err_msg}\n{str(e)}")
                    errors.append(err_msg)

            else:
                err_msg = f"Login failed with status code {res.status_code}"
                logger.error(f"{err_msg}")
                errors.append(err_msg)
        except Exception as e:
            err_msg = "Error at the end"
            logger.error(f"{err_msg}\n{str(e)}")
            errors.append(err_msg)

        cmd_name = __name__.split(".")[-1].replace("_", " ").upper()
        err_str = (
            f'<strong style="color: red;">Errors: {len(errors)}</strong>'
            if len(errors) > 0
            else '<strong style="color: green;">Errors: 0</strong>'
        )
        msg = "<p>{} completed. Errors: {}. IDs updated: {}.</p>".format(
            cmd_name, err_str, updates
        )
        logger.info(msg)
