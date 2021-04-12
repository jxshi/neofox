#
# Copyright (c) 2020-2030 Translational Oncology at the Medical Center of the Johannes Gutenberg-University Mainz gGmbH.
#
# This file is part of Neofox
# (see https://github.com/tron-bioinformatics/neofox).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.#
from logzero import logger
from unittest import TestCase

from neofox.model.mhc_parser import MhcParser
from neofox.model.neoantigen import Mutation

from neofox.model.conversion import ModelConverter, ModelValidator
import neofox.tests.integration_tests.integration_test_tools as integration_test_tools
from neofox.helpers.runner import Runner
from neofox.MHC_predictors.netmhcpan.combine_netmhcpan_pred_multiple_binders import (
    BestAndMultipleBinder,
)
from neofox.MHC_predictors.netmhcpan.netmhcpan_prediction import NetMhcPanPredictor
from neofox.MHC_predictors.netmhcpan.combine_netmhcIIpan_pred_multiple_binders import (
    BestAndMultipleBinderMhcII,
)
from neofox.MHC_predictors.netmhcpan.netmhcIIpan_prediction import NetMhcIIPanPredictor


class TestBestMultipleBinder(TestCase):
    def setUp(self):
        references, self.configuration = integration_test_tools.load_references()
        self.runner = Runner()
        self.available_alleles_mhc1 = (
            references.get_available_alleles().get_available_mhc_i()
        )
        self.available_alleles_mhc2 = (
            references.get_available_alleles().get_available_mhc_ii()
        )
        self.hla_database = references.get_hla_database()
        self.mhc_parser = MhcParser(self.hla_database)
        self.test_mhc_one = integration_test_tools.get_mhc_one_test(self.hla_database)
        self.test_mhc_two = integration_test_tools.get_mhc_two_test(self.hla_database)

    def test_best_multiple_run(self):
        best_multiple = BestAndMultipleBinder(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        # this is some valid example neoantigen candidate sequence
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="DEVLGEPSQDILVTDQTRLEATISPET",
                wild_type_xmer="DEVLGEPSQDILVIDQTRLEATISPET",
            )
        )
        best_multiple.run(
            mutation=mutation,
            mhc1_alleles_patient=self.test_mhc_one,
            mhc1_alleles_available=self.available_alleles_mhc1,
        )
        self.assertEqual(543.9, best_multiple.best_epitope_by_affinity.affinity_score)
        self.assertEqual('HLA-A*02:01', best_multiple.best_epitope_by_affinity.hla)
        self.assertEqual(0.4304, best_multiple.best_epitope_by_rank.rank)
        self.assertEqual('HLA-C*05:01', best_multiple.best_epitope_by_rank.hla)
        self.assertEqual("VTDQTRLEA", best_multiple.best_epitope_by_rank.peptide)
        self.assertEqual(
            best_multiple.best_ninemer_epitope_by_rank.hla,
            best_multiple.best_ninemer_wt_epitope_by_rank.hla,
        )
        logger.info(best_multiple.best_epitope_by_rank.peptide)
        logger.info(best_multiple.phbr_i)

    def test_phbr1(self):
        best_multiple = BestAndMultipleBinder(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        netmhcpan = NetMhcPanPredictor(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="DEVLGEPSQDILVTDQTRLEATISPET",
                wild_type_xmer="DEVLGEPSQDILVIDQTRLEATISPET",
            )
        )
        # all alleles = heterozygous
        predictions = netmhcpan.mhc_prediction(
            self.test_mhc_one, self.available_alleles_mhc1, mutation.mutated_xmer
        )

        predicted_neoepitopes = netmhcpan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        best_epitopes_per_allele = (
            BestAndMultipleBinder.extract_best_epitope_per_alelle(
                predicted_neoepitopes, self.test_mhc_one
            )
        )
        phbr_i = best_multiple.calculate_phbr_i(best_epitopes_per_allele, self.test_mhc_one)
        self.assertIsNotNone(phbr_i)
        self.assertAlmostEqual(1.9449989270, phbr_i)
        # one homozygous allele present
        mhc_alleles = ModelConverter.parse_mhc1_alleles(
            [
                "HLA-A*24:02",
                "HLA-A*02:01",
                "HLA-B*15:01",
                "HLA-B*44:02",
                "HLA-C*05:01",
                "HLA-C*05:01",
            ], self.hla_database
        )
        predictions = netmhcpan.mhc_prediction(
            self.test_mhc_one, self.available_alleles_mhc1, mutation.mutated_xmer
        )

        predicted_neoepitopes = netmhcpan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        best_epitopes_per_allele = (
            BestAndMultipleBinder.extract_best_epitope_per_alelle(
                predicted_neoepitopes, mhc_alleles
            )
        )
        phbr_i = best_multiple.calculate_phbr_i(best_epitopes_per_allele, mhc_alleles)
        self.assertIsNotNone(phbr_i)
        self.assertAlmostEqual(1.131227969630, phbr_i)
        # mo info for one allele
        mhc_alleles = ModelConverter.parse_mhc1_alleles(
            ["HLA-A*24:02", "HLA-A*02:01", "HLA-B*15:01", "HLA-B*44:02", "HLA-C*05:01"], self.hla_database
        )

        predictions = netmhcpan.mhc_prediction(
            self.test_mhc_one, self.available_alleles_mhc1, mutation.mutated_xmer
        )
        predicted_neoepitopes = netmhcpan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        best_epitopes_per_allele = (
            BestAndMultipleBinder.extract_best_epitope_per_alelle(
                predicted_neoepitopes, mhc_alleles
            )
        )
        phbr_i = best_multiple.calculate_phbr_i(best_epitopes_per_allele, mhc_alleles)
        self.assertIsNone(phbr_i)

    def test_best_multiple_mhc2_run(self):
        best_multiple = BestAndMultipleBinderMhcII(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        # this is some valid example neoantigen candidate sequence
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="DEVLGEPSQDILVTDQTRLEATISPET",
                wild_type_xmer="DEVLGEPSQDILVIDQTRLEATISPET",
            )
        )
        best_multiple.run(
            mutation=mutation,
            mhc2_alleles_patient=self.test_mhc_two,
            mhc2_alleles_available=self.available_alleles_mhc2,
        )
        logger.info(best_multiple.best_predicted_epitope_rank.rank)
        logger.info(best_multiple.best_predicted_epitope_affinity.affinity_score)
        logger.info(best_multiple.best_predicted_epitope_rank.peptide)
        logger.info(best_multiple.phbr_ii)
        self.assertEqual(17.0, best_multiple.best_predicted_epitope_rank.rank)
        self.assertEqual(
            1434.66, best_multiple.best_predicted_epitope_affinity.affinity_score
        )
        self.assertEqual(
            "VTDQTRLEATISPET", best_multiple.best_predicted_epitope_rank.peptide
        )

    def test_phbr2(self):
        best_multiple = BestAndMultipleBinderMhcII(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        netmhc2pan = NetMhcIIPanPredictor(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="DEVLGEPSQDILVTDQTRLEATISPET",
                wild_type_xmer="DEVLGEPSQDILVIDQTRLEATISPET",
            )
        )
        # all alleles = heterozygous
        allele_combinations = netmhc2pan.generate_mhc2_alelle_combinations(self.test_mhc_two)
        patient_mhc2_isoforms = best_multiple._get_only_available_combinations(
            allele_combinations, self.available_alleles_mhc2
        )
        predictions = netmhc2pan.mhcII_prediction(
            patient_mhc2_isoforms, mutation.mutated_xmer
        )
        filtered_predictions = netmhc2pan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        logger.info(filtered_predictions)
        logger.info(self.test_mhc_two)
        best_predicted_epitopes_per_alelle = (
            best_multiple.extract_best_epitope_per_mhc2_alelle(predictions=filtered_predictions, mhc_isoforms=self.test_mhc_two
            )
        )
        logger.info(best_predicted_epitopes_per_alelle)
        logger.info(len(best_predicted_epitopes_per_alelle))
        phbr_ii = best_multiple.calculate_phbr_ii(best_predicted_epitopes_per_alelle)
        self.assertIsNotNone(phbr_ii)
        self.assertAlmostEqual(37.09795868, phbr_ii)
        # mo info for one allele
        mhc2_alleles = ModelConverter.parse_mhc2_alleles(
            [
                "HLA-DRB1*04:02",
                "HLA-DRB1*08:01",
                "HLA-DQA1*03:01",
                "HLA-DQA1*04:01",
                "HLA-DQB1*03:02",
                "HLA-DQB1*04:02",
                "HLA-DPA1*01:03",
                "HLA-DPA1*02:01",
                "HLA-DPB1*13:01",
                "HLA-DPB1*13:01",
            ], self.hla_database
        )

        allele_combinations = netmhc2pan.generate_mhc2_alelle_combinations(mhc2_alleles)
        patient_mhc2_isoforms = best_multiple._get_only_available_combinations(
            allele_combinations, self.available_alleles_mhc2
        )
        predictions = netmhc2pan.mhcII_prediction(
            patient_mhc2_isoforms, mutation.mutated_xmer
        )
        filtered_predictions = netmhc2pan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        best_predicted_epitopes_per_alelle = (
            best_multiple.extract_best_epitope_per_mhc2_alelle(
                filtered_predictions, mhc2_alleles
            )
        )
        logger.info(best_predicted_epitopes_per_alelle)
        logger.info(len(best_predicted_epitopes_per_alelle))
        phbr_ii = best_multiple.calculate_phbr_ii(best_predicted_epitopes_per_alelle)
        self.assertIsNotNone(phbr_ii)
        self.assertAlmostEqual(37.7107933753, phbr_ii)

        # one allele present
        mhc2_alleles = ModelConverter.parse_mhc2_alleles(
            [
                "HLA-DRB1*04:02",
                "HLA-DRB1*08:01",
                "HLA-DQA1*03:01",
                "HLA-DQA1*04:01",
                "HLA-DQB1*03:02",
                "HLA-DQB1*04:02",
                "HLA-DPA1*01:03",
                "HLA-DPA1*02:01",
                "HLA-DPB1*13:01",
            ],
            self.hla_database
        )
        allele_combinations = netmhc2pan.generate_mhc2_alelle_combinations(mhc2_alleles)
        patient_mhc2_isoforms = best_multiple._get_only_available_combinations(
            allele_combinations, self.available_alleles_mhc2
        )
        predictions = netmhc2pan.mhcII_prediction(
            patient_mhc2_isoforms, mutation.mutated_xmer
        )
        filtered_predictions = netmhc2pan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        best_predicted_epitopes_per_alelle = (
            best_multiple.extract_best_epitope_per_mhc2_alelle(
                filtered_predictions, mhc2_alleles
            )
        )
        logger.info(best_predicted_epitopes_per_alelle)
        logger.info(len(best_predicted_epitopes_per_alelle))
        phbr_ii = best_multiple.calculate_phbr_ii(best_predicted_epitopes_per_alelle)
        self.assertIsNone(phbr_ii)

    def test_generator_rate(self):
        best_multiple = BestAndMultipleBinder(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        netmhcpan = NetMhcPanPredictor(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="DRAIPLVLVSGNHYIGNTPTAETVEEF",
                wild_type_xmer="DRAIPLVLVSGNHDIGNTPTAETVEEF",
            )
        )
        # all alleles = heterozygous
        predictions = netmhcpan.mhc_prediction(
            self.test_mhc_one, self.available_alleles_mhc1, mutation.mutated_xmer
        )

        predictions_wt = netmhcpan.mhc_prediction(
            self.test_mhc_one, self.available_alleles_mhc1, mutation.wild_type_xmer
        )

        predicted_neoepitopes = netmhcpan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        filtered_predictions_wt = netmhcpan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions_wt
        )

        generator_rate_ADN = best_multiple.determine_number_of_alternative_binders(
            predictions=predicted_neoepitopes, predictions_wt=filtered_predictions_wt
        )
        generator_rate_CDN = best_multiple.determine_number_of_binders(
            predictions=predicted_neoepitopes, threshold=50
        )
        self.assertEqual(generator_rate_ADN, 8)
        logger.info(generator_rate_ADN)
        self.assertEqual(generator_rate_CDN, 1)
        logger.info(generator_rate_CDN)

    def test_generator_rate_mhcII(self):
        best_multiple = BestAndMultipleBinderMhcII(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        netmhc2pan = NetMhcIIPanPredictor(
            runner=self.runner, configuration=self.configuration, mhc_parser=self.mhc_parser
        )
        mutation = ModelValidator._validate_mutation(
            Mutation(
                mutated_xmer="RTNLLAALHRSVRWRAADQGHRSAFLV",
                wild_type_xmer="RTNLLAALHRSVRRRAADQGHRSAFLV",
            )
        )
        # all alleles = heterozygous
        allele_combinations = netmhc2pan.generate_mhc2_alelle_combinations(self.test_mhc_two)
        patient_mhc2_isoforms = best_multiple._get_only_available_combinations(
            allele_combinations, self.available_alleles_mhc2
        )
        predictions = netmhc2pan.mhcII_prediction(
            patient_mhc2_isoforms, mutation.mutated_xmer
        )

        predictions_wt = netmhc2pan.mhcII_prediction(
            patient_mhc2_isoforms, mutation.wild_type_xmer
        )

        predicted_neoepitopes = netmhc2pan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions
        )
        filtered_predictions_wt = netmhc2pan.filter_binding_predictions(
            position_of_mutation=mutation.position, predictions=predictions_wt
        )

        generator_rate_ADN = best_multiple.determine_number_of_alternative_binders(
            predictions=predicted_neoepitopes, predictions_wt=filtered_predictions_wt
        )
        generator_rate_CDN = best_multiple.determine_number_of_binders(
            predictions=predicted_neoepitopes
        )
        self.assertEqual(generator_rate_ADN, 2)
        self.assertEqual(generator_rate_CDN, 8)
        logger.info(generator_rate_ADN)
        logger.info(generator_rate_CDN)
