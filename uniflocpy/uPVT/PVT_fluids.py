# -*- coding: utf-8 -*-
"""
Created on Mon Sept 04 2017

@author: rnt

UniflocPy

класс для расчета uPVT свойств углеводородных флюидов и воды

"""
import unittest
import uniflocpy.uTools.uconst as uc
import uniflocpy.uPVT.PVT_correlations as PVT
import math

class FluidBlackOil:
    """
    Описание смеси нефти, газа и воды по модели нелетучей нефти
    
    Описание флюида - скважинной продукции
    Класс обеспечивает расчет свойств флюида при заданных термобарических условиях
    по одному набору корреляционных зависимостей
    классы потомки могут менять набор корреляционных зависимостей для уточнения расчета
    """
    _pb_cal: float

    def __init__(self, gamma_oil=0.86, gamma_gas=0.6, gamma_wat=1.0, rsb_m3m3=200.0, gamma_gassp=0, y_h2s=0, y_co2=0,
                 y_n2=0, s_ppm=0, par_wat=0, pbcal_bar=-1., tpb_C=80, bobcal_m3m3=1.2, muobcal_cP=0.5 ):
        """
        создает флюид с заданными базовыми свойствами

        калибровочные параметры при необходимости надо задавать отдельно
        :param gamma_oil:
        :param gamma_gas:
        :param gamma_wat:
        :param rsb_m3m3:
        :param gamma_gassp:
        """
        self.gamma_gas = gamma_gas              # specific gravity of gas (by air), dimensionless
        self.gamma_oil = gamma_oil              # specific gravity of oil
        self.gamma_wat = gamma_wat              # specific gravity of water
        self.rsb_m3m3 = rsb_m3m3                # solution gas ratio at bubble point
        self.gamma_gassp = gamma_gassp          # specific gas density in separator(by air)
        self.y_h2s = y_h2s                      # mole fraction of the hydrogen sulfide
        self.y_co2 = y_co2                      # mole fraction of the carbon dioxide
        self.y_n2 = y_n2                        # mole fraction of the nitrogen
        self.s_ppm = s_ppm                      # water salinity
        self.par_wat = par_wat                  # 0 = pure water, 1 = brine , 2 = brine with dissolved methane
        # термобарические условия
        self.p_bar = uc.psc_bar                 # thermobaric conditions for all parameters
        self.t_c = uc.tsc_c                     # can be set up by calc method
        # калибровочные параметры
        self.pbcal_bar = pbcal_bar            # давление насыщения, калибровочный параметр
        self.tpb_C = tpb_C
        self.bobcal_m3m3 = bobcal_m3m3
        self.muobcal_cP = muobcal_cP

        # расчетные параметры доступны только для чтения через свойства
        self._pb_bar = 0.0
        self._bob_m3m3 = 0.0
        self._muob_cP = 0.0
        self.tpb_C = 0.0
        self._mu_oil_cP = 0.0        # TODO хорошо бы везде сделать единообразные индексы для нефти или o или oil
        self._mu_gas_cP = 0.0
        self._mu_wat_cP = 0.0
        self._mu_deadoil_cP = 0.0    # dead oil
        self._rho_oil_kgm3 = 0.0
        self._rho_gas_kgm3 = 0.0
        self._rho_wat_kgm3 = 0.0
        self._rs_m3m3 = 0.0
        self._rsw_m3m3 = 0.0   # TODO проверить - равен GWR?
        self._bo_m3m3 = 0.0
        self._bg_m3m3 = 0.0
        self._bw_m3m3 = 0.0
        self._z = 0.0
        self._compr_oil_1bar = 0.0
        self._compr_gas_1bar = 0.0
        self._compr_wat_1bar = 0.0
        self._heatcap_oil_jkgc = 0.0
        self._heatcap_gas_jkgc = 0.0
        self._heatcap_wat_jkgc = 0.0
        self._sigma_oil_gas_Nm = 0.0
        self._sigma_wat_gas_Nm = 0.0
        self._thermal_conduct_oil_wmk = 0.0
        self._thermal_conduct_gas_wmk = 0.0
        self._thermal_conduct_wat_wmk = 0.0
        self._thermal_expansion_wat_1c = 0.0

    # ========= default properties definition =======
    @property
    def pb_bar(self):
        """ return bubble point pressure an bar absolute"""
        return self._pb_bar

    @property
    def mu_oil_cP(self):
        """ return oil viscosity at working condition"""
        return self._mu_oil_cP

    @property
    def mu_gas_cP(self):
        """ return gas viscosity at working condition"""
        return self._mu_gas_cP

    @property
    def mu_wat_cP(self):
        """ return water viscosity at working condition"""
        return self._mu_wat_cP

    @property
    def rho_oil_kgm3(self):
        """ return oil density at working condition"""
        return self._rho_oil_kgm3

    @property
    def rho_oil_stkgm3(self):
        """ return oil density at working condition"""
        return self.gamma_oil * uc.rho_w_kgm3_sc

    @property
    def rho_gas_kgm3(self):
        """ return gas density at working condition"""
        return self._rho_gas_kgm3

    @property
    def rho_wat_kgm3(self):
        """ return water density at working condition"""
        return self._rho_wat_kgm3

    @property
    def rs_m3m3(self):
        """ return gas oil solution ratio at working condition"""
        return self._rs_m3m3

    @property
    def rsw_m3m3(self):
        """ return gas water solution ratio at working condition"""
        return self._rsw_m3m3

    @property
    def bo_m3m3(self):
        """ return oil formation volume factor at working condition"""
        return self._bo_m3m3

    @property
    def bg_m3m3(self):
        """ return gas formation volume factor at working condition"""
        return self._bg_m3m3

    @property
    def bw_m3m3(self):
        """ return water formation volume factor at working condition"""
        return self._bw_m3m3

    @property
    def z(self):
        """ return gas z factor (compressibility) at working condition"""
        return self._z

    @property
    def compr_oil_1bar(self):
        """ return oil compressibility at working condition"""
        return self._compr_oil_1bar

    @property
    def compr_gas_1bar(self):
        """ return gas compressibility at working condition"""
        return self._compr_gas_1bar

    @property
    def compr_wat_1bar(self):
        """ return water compressibility at working condition"""
        return self._compr_wat_1bar

    @property
    def heatcap_oil_jkgc(self):
        """ return oil heat capacity at working condition"""
        return self._heatcap_oil_jkgc

    @property
    def heatcap_gas_jkgc(self):
        """ return gas heat capacity at working condition"""
        return self._heatcap_gas_jkgc

    @property
    def heatcap_wat_jkgc(self):
        """ return water heat capacity at working condition"""
        return self._heatcap_wat_jkgc

    @property
    def thermal_conduct_oil_wmk(self):
        """ return oil thermal conductivity at working condition"""
        return self._thermal_conduct_oil_wmk

    @property
    def thermal_conduct_gas_wmk(self):
        """ return gas thermal conductivity at working condition"""
        return self._thermal_conduct_gas_wmk

    @property
    def thermal_conduct_wat_wmk(self):
        """ return water thermal conductivity at working condition"""
        return self._thermal_conduct_wat_wmk

    @property
    def thermal_expansion_wat_1c(self):
        """ return water thermal expansion coefficient at working condition"""
        return self._thermal_expansion_wat_1c

    @property
    def sigma_oil_gas_Nm(self):
        """ return oil surface tension  at working condition"""
        return self._sigma_oil_gas_Nm

    @property
    def sigma_wat_gas_Nm(self):
        """ return water surface tension at working condition"""
        return self._sigma_wat_gas_Nm

    @property
    def rho_gas_sckgm3(self):
        """ component density at standard condition, read only """
        return self.gamma_gas * uc.air_density_sckgm3

    def calc(self, p_bar, t_c):
        """ recalculate all parameters according to some pressure and temperature"""
        # это абстрактный класс, сюда можно вставить упрощенную реализацию свойств прямыми линиями
        # абстрактный класс не подразумевает реализии, его задача упростить создание потомков
        # которые и должны использоваться в реальной работе
        self.p_bar = p_bar
        self.t_c = t_c
        pass


class FluidStanding(FluidBlackOil):  # TODO после проверки свойств добавить их в FluidMcCain
    """
    класс, реализующий расчет свойств нефти с использованием
    набора корреляций на основе Standing
    """

    def calc(self, p_bar, t_c):
        """Расчет свойств нефти на основе набора корреляций Standing"""
        super().calc(p_bar, t_c)
        # подготовим внутренние переменные для расчетов
        p_MPaa = uc.bar2MPa(self.p_bar)
        pbcal_MPaa = uc.bar2MPa(self.pbcal_bar)
        t_K = uc.c2k(self.t_c)

        # oil
        # найдем значение давления насыщения по Standing
        pb_MPaa = PVT.unf_pb_Standing_MPaa(self.rsb_m3m3, self.gamma_oil, self.gamma_gas, t_K)
        self._pb_bar = uc.MPa2bar(pb_MPaa)
        # TODO необходимо будет сделать калибровку при любом P,T любого свойства
        if pbcal_MPaa > 0:
            p_fact = pb_MPaa / pbcal_MPaa
            # сдвигаем шкалу по давлению для расчета, если задана калибровка
            p_MPaa = p_fact * p_MPaa
            self._pb_bar = self._pb_bar / p_fact
        # внутри rs есть проверка на давление насыщения
        self._rs_m3m3 = PVT.unf_rs_Standing_m3m3(p_MPaa, pb_MPaa, self.rsb_m3m3, self.gamma_oil, self.gamma_gas, t_K)
        co_1MPa = PVT.unf_compressibility_oil_VB_1Mpa(self._rs_m3m3, t_K, self.gamma_oil, p_MPaa, self.gamma_gas)
        self._compr_oil_1bar = uc.compr_1mpa_2_1bar(co_1MPa)
        # оценим значение объемного коэффициента
        # оценим значение объемного коэффициента при давлении насыщения
        self._bob_m3m3 = PVT.unf_fvf_Standing_m3m3_saturated(self.rsb_m3m3, self.gamma_gas, self.gamma_oil, t_K)
        if p_MPaa > pb_MPaa:
            self._bo_m3m3 = PVT.unf_fvf_VB_m3m3_above(self._bob_m3m3, co_1MPa, pb_MPaa, p_MPaa)
        else:
            self._bo_m3m3 = PVT.unf_fvf_Standing_m3m3_saturated(self._rs_m3m3, self.gamma_gas, self.gamma_oil, t_K)
        # проверим необходимость калибровки значения объемного коэффициента
        #if self.bobcal_m3m3 > 0:  # TODO проверить калибровку, с ней неправильно считает
        #    b_fact = (self._bob_m3m3 - 1) / (self.bobcal_m3m3 - 1)
        #    self._bo_m3m3 = b_fact * self._bo_m3m3
        self._rho_oil_kgm3 = PVT.unf_density_oil_Standing(p_MPaa, pb_MPaa, co_1MPa, self._rs_m3m3, self._bo_m3m3,
                                                          self.gamma_gas, self.gamma_oil)
        # оценим значение вязкости
        self._mu_deadoil_cP = PVT.unf_deadoilviscosity_Beggs_cP(self.gamma_oil, t_K)
        self._muob_cP = PVT.unf_saturatedoilviscosity_Beggs_cP(self._mu_deadoil_cP, self.rsb_m3m3)
        self._mu_oil_cP = PVT.unf_oil_viscosity_Beggs_VB_cP(self._mu_deadoil_cP, self._rs_m3m3, p_MPaa, pb_MPaa)
        if self.muobcal_cP > 0:
            mu_fact = self.muobcal_cP / self._muob_cP
            self._mu_oil_cP = mu_fact * self._mu_oil_cP

        # определим термодинамические свойства нефти
        self._heatcap_oil_jkgc = PVT.unf_heat_capacity_oil_Gambill_JkgC(self.gamma_oil, self.t_c)
        self._thermal_conduct_oil_wmk = PVT.unf_thermal_conductivity_oil_Cragoe_WmK(self.gamma_oil, self.t_c)


        # gas
        tpc_K = PVT.unf_pseudocritical_temperature_K(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)
        ppc_MPa = PVT.unf_pseudocritical_pressure_MPa(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)
        self._z = PVT.unf_zfactor_DAK(p_MPaa, t_K, ppc_MPa, tpc_K)
        self._mu_gas_cP = PVT.unf_gasviscosity_Lee_cP(t_K, p_MPaa, self._z, self.gamma_gas)
        self._bg_m3m3 = PVT.unf_gas_fvf_m3m3(t_K, p_MPaa, self._z)
        self._compr_gas_1bar = uc.compr_1mpa_2_1bar(PVT.unf_compressibility_gas_Mattar_1MPa(p_MPaa, t_K,
                                                                                            ppc_MPa, tpc_K))
        self._rho_gas_kgm3 = PVT.unf_gas_density_kgm3(t_K, p_MPaa, self.gamma_gas, self._z)

        # определим термодинамические свойства газа
        self._heatcap_gas_jkgc = PVT.unf_heat_capacity_gas_Mahmood_Moshfeghian_JkgC(p_MPaa, t_K, self.gamma_gas)
        self._thermal_conduct_gas_wmk = PVT.unf_thermal_conductivity_gas_methane_WmK(self.t_c)

        # water
        # TODO НУЖНО проверить GWR
        self._rho_wat_kgm3 = PVT.unf_density_brine_Spivey_kgm3(t_K, p_MPaa, self.s_ppm, self.par_wat)
        self._compr_wat_1bar = uc.compr_1mpa_2_1bar(PVT.unf_compressibility_brine_Spivey_1MPa(t_K, p_MPaa, self.s_ppm,
                                                                                              self._z, self.par_wat))
        self._bw_m3m3 = PVT.unf_fvf_brine_Spivey_m3m3(t_K, p_MPaa, self.s_ppm)
        self._mu_wat_cP = PVT.unf_viscosity_brine_MaoDuan_cP(t_K, p_MPaa, self.s_ppm)
        self._rsw_m3m3 = PVT.unf_gwr_brine_Spivey_m3m3(self.s_ppm, self._z)
        # определим термодинамические свойства воды
        self._heatcap_wat_jkgc = PVT.unf_heat_capacity_water_IAPWS_JkgC(self.t_c)
        self._thermal_conduct_wat_wmk = PVT.unf_thermal_conductivity_water_IAPWS_WmC(self.t_c)
        self._thermal_expansion_wat_1c = PVT.unf_thermal_expansion_coefficient_water_IAPWS_1C(self.t_c)

        # определим свойства системы
        self._sigma_oil_gas_Nm = PVT.unf_surface_tension_go_Baker_Swerdloff_Nm(t_K, self.gamma_oil, p_MPaa)
        self._sigma_wat_gas_Nm = PVT.unf_surface_tension_gw_Sutton_Nm(self.rho_wat_kgm3, self.rho_gas_kgm3, self.t_c)
        return 1


class FluidMcCain(FluidBlackOil):
    """
    класс, реализующий расчет свойств нефти с использованием
    набора корреляций на основе McCain
    """

    def calc(self, p_bar, t_c):
        """Расчет свойств нефти на основе набора корреляций McCain"""
        super().calc(p_bar, t_c)
        # подготовим внутренние переменные для расчетов
        p_MPaa = uc.bar2MPa(self.p_bar)
        pbcal_MPaa = uc.bar2MPa(self.pbcal_bar)
        t_K = uc.c2k(self.t_c)
        # найдем значение давления насыщения по Valko McCain
        pb_MPaa = PVT.unf_pb_Valko_MPaa(self.rsb_m3m3, self.gamma_oil, self.gamma_gas, t_K)
        self._pb_bar = uc.MPa2bar(pb_MPaa)
        # TODO необходимо будет сделать калибровку при любом P,T любого свойства
        if pbcal_MPaa > 0:
            p_fact = pb_MPaa / pbcal_MPaa
            # сдвигаем шкалу по давлению для расчета, если задана калибровка
            p_MPaa = p_fact * p_MPaa
            self._pb_bar = self._pb_bar/p_fact
        # внутри rs есть проверка на давление насыщения
        self._rs_m3m3 = PVT.unf_rs_Velarde_m3m3(p_MPaa, pb_MPaa, self.rsb_m3m3, self.gamma_oil, self.gamma_gas, t_K)
        co_1MPa = PVT.unf_compressibility_oil_VB_1Mpa(self._rs_m3m3, t_K, self.gamma_oil, p_MPaa, self.gamma_gas)
        self._compr_oil_1bar = uc.compr_1mpa_2_1bar(co_1MPa)
        # внутри rho есть проверка на давление насыщения
        self._rho_oil_kgm3 = PVT.unf_density_oil_Mccain(p_MPaa, pb_MPaa, co_1MPa, self._rs_m3m3, self.gamma_gas, t_K,
                                                        self.gamma_oil, self.gamma_gassp)
        # оценим значение объемного коэффициента
        # оценим значение объемного коэффициента при давлении насыщения
        self._bob_m3m3 = PVT.unf_fvf_Mccain_m3m3_below(self.rho_oil_stkgm3, self.rsb_m3m3, self._rho_oil_kgm3,
                                                       self.gamma_gas)
        if p_MPaa > pb_MPaa:
            self._bo_m3m3 = PVT.unf_fvf_VB_m3m3_above(self._bob_m3m3, co_1MPa, pb_MPaa, p_MPaa)
        else:
            self._bo_m3m3 = PVT.unf_fvf_Mccain_m3m3_below(self.rho_oil_stkgm3, self._rs_m3m3, self._rho_oil_kgm3,
                                                          self.gamma_gas)
        # проверим необходимость калибровки значения объемного коэффициента
        #if self.bobcal_m3m3 > 0:
        #    b_fact = (self._bob_m3m3 - 1) / (self.bobcal_m3m3 - 1)
        #    self._bo_m3m3 = b_fact * self._bo_m3m3
        # оценим значение вязкости
        self._mu_deadoil_cP = PVT.unf_deadoilviscosity_Beggs_cP(self.gamma_oil, t_K)
        self._muob_cP = PVT.unf_saturatedoilviscosity_Beggs_cP(self._mu_deadoil_cP, self.rsb_m3m3)
        self._mu_oil_cP = PVT.unf_oil_viscosity_Beggs_VB_cP(self._mu_deadoil_cP, self._rs_m3m3, p_MPaa, pb_MPaa)
        if self.muobcal_cP > 0:
            mu_fact = self.muobcal_cP / self._muob_cP
            self._mu_oil_cP = mu_fact * self._mu_oil_cP
        # gas
        tpc_K = PVT.unf_pseudocritical_temperature_K(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)
        ppc_MPa = PVT.unf_pseudocritical_pressure_MPa(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)
        self._z = PVT.unf_zfactor_DAK(p_MPaa, t_K, ppc_MPa, tpc_K)
        self._mu_gas_cP = PVT.unf_gasviscosity_Lee_cP(t_K, p_MPaa, self._z, self.gamma_gas)
        self._bg_m3m3 = PVT.unf_gas_fvf_m3m3(t_K, p_MPaa, self._z)
        self._compr_gas_1bar = uc.compr_1mpa_2_1bar(PVT.unf_compressibility_gas_Mattar_1MPa(p_MPaa, t_K,
                                                                                            ppc_MPa, tpc_K))
        self._rho_gas_kgm3 = PVT.unf_gas_density_kgm3(t_K, p_MPaa, self.gamma_gas, self._z)
        # water
        # TODO НУЖНО ДОБАВИТЬ GWR
        self._rho_wat_kgm3 = PVT.unf_density_brine_Spivey_kgm3(t_K, p_MPaa, self.s_ppm, self.par_wat)
        self._compr_wat_1bar = uc.compr_1mpa_2_1bar(PVT.unf_compressibility_brine_Spivey_1MPa(t_K, p_MPaa, self.s_ppm,     
                                                                                              self._z, self.par_wat))
        self._bw_m3m3 = PVT.unf_fvf_brine_Spivey_m3m3(t_K, p_MPaa, self.s_ppm)
        self._mu_wat_cP = PVT.unf_viscosity_brine_MaoDuan_cP(t_K, p_MPaa, self.s_ppm)
        return 1


class FluidFlow:
    """класс для описания потока флюида"""
    def __init__(self, fluid = FluidStanding()):
        self.fl = fluid  # по умолчанию задаем какой то флюид

        self.qliq_on_surface_m3day = 100      # дебит жидкости
        self.fw_on_surface_perc = 20              # обводненность
        self.d_m = 0.152  # внутренний диаметр трубы

        self.qoil_on_surface_m3day = None
        self.qwat_on_surface_m3day = None
        self.qgas_on_surface_m3day = None
        self.Ap_m2 = None

        self.qoil_m3day = None
        self.qwat_m3day = None
        self.qgas_m3day = None
        self.qliq_m3day = None

        self.vsl_msec = None
        self.vsg_msec = None
        self.vsm_msec = None

        self.liquid_content = None
        self.fw_perc = None

        self.rho_liq_kgm3 = None
        self.sigma_liq_Nm = None
        self.mu_liq_cP = None

        self.mun_cP = None
        self.rhon_kgm3 = None

    def calc(self, p_bar, t_c):
        """расчет свойств потока для заданных термобарических условий"""

        self.fl.calc(p_bar, t_c)

        self.Ap_m2 = math.pi * self.d_m ** 2 / 4

        self.qoil_on_surface_m3day = self.qliq_on_surface_m3day * (1 - self.fw_on_surface_perc / 100)

        self.qwat_on_surface_m3day = self.qliq_on_surface_m3day * self.fw_on_surface_perc / 100

        self.qgas_on_surface_m3day = self.qoil_on_surface_m3day * self.fl.rsb_m3m3  # TODO учесть газ в воде

        self.qoil_m3day = self.qoil_on_surface_m3day * self.fl.bo_m3m3

        self.qwat_m3day = self.qwat_on_surface_m3day * self.fl.bw_m3m3

        self.qliq_m3day = self.qoil_m3day + self.qwat_m3day
        # TODO учесть газ в воде
        self.qgas_m3day = (self.qgas_on_surface_m3day - self.qoil_on_surface_m3day * self.fl.rs_m3m3) * self.fl.bg_m3m3

        self.vsl_msec = uc.m3day2m3sec(self.qliq_m3day) / self.Ap_m2

        self.vsg_msec = uc.m3day2m3sec(self.qgas_m3day) / self.Ap_m2

        self.vsm_msec = self.vsl_msec + self.vsg_msec

        self.liquid_content = self.qliq_m3day / (self.qliq_m3day + self.qgas_m3day)

        self.fw_perc = self.qwat_m3day / (self.qwat_m3day + self.qoil_m3day) * 100

        self.rho_liq_kgm3 = self.fl.rho_oil_kgm3 * ( 1 - self.fw_perc / 100) + self.fl.rho_wat_kgm3 * self.fw_perc / 100

        self.sigma_liq_Nm = self.fl.sigma_oil_gas_Nm * (1 - self.fw_perc / 100) + self.fl.sigma_wat_gas_Nm * self.fw_perc / 100

        self.mu_liq_cP = self.fl.mu_oil_cP * (1 - self.fw_perc / 100) + self.fl.mu_wat_cP * self.fw_perc / 100

        self.mun_cP = self.mu_liq_cP * self.liquid_content + self.fl.mu_gas_cP * (1 - self.liquid_content)

        self.rhon_kgm3 = self.rho_liq_kgm3 * self.liquid_content + self.fl.rho_gas_kgm3 * (1 - self.liquid_content)

    # здесь будут методы для расчета свойств потока, также можно сделать трансляцию базовых свойств (pb, rs)
    # идея отдельного класса - тут вообще говоря может быть и смесь флюидов - какой то потомок может расшириться туда
