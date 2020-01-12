import os
import sys
sys.path.append('../'*4)
import pandas as pd

class all_ESP_data():  # класс, в котором хранятся данные
    def __init__(self, UniflocVBA, tr_data):
        """
        класс для хранение и доступа ко всем данным скважины - входным, выходным
        :param UniflocVBA: текущая надстройка UniflocVBA API
        :param tr_data: данные техрежима
        """
        self.ESP_rate_nom = tr_data.esp_nom_rate_m3day
        self.esp_id = UniflocVBA.calc_ESP_id_by_rate(self.ESP_rate_nom)
        self.ESP_head_nom = tr_data.esp_nom_head_m
        self.dcas_mm = tr_data.d_cas_mm
        self.h_pump_m = tr_data.h_pump_m
        self.d_tube_mm = tr_data.d_tube_mm
        self.p_cas_data_atm = -1  # нет расчета затрубного пространства - он долгий и немножко бесполезный

        self.eff_motor_d = 0.89
        self.i_motor_nom_a = tr_data.i_motor_nom_a
        self.power_motor_nom_kwt = tr_data.power_motor_nom_kwt
        self.h_tube_m = self.h_pump_m  # ТР
        self.h_perf_m = self.h_pump_m + 1  # ТР
        self.udl_m = tr_data.udl_m  # ТР

        self.c_calibr_rate_d = 1

        self.ksep_d = 0.7  # ТР
        self.KsepGS_fr = 0.7  # ТР
        self.hydr_corr = 1  # 0 - BB, 1 - Ansari
        self.gamma_oil = 0.945
        self.gamma_gas = 0.9
        self.gamma_wat = 1.011
        self.rsb_m3m3 = 29.25
        self.tres_c = 16
        self.pb_atm = 40
        self.bob_m3m3 = 1.045
        self.muob_cp = 100
        self.rp_m3m3 = 30

        self.psep_atm = None
        self.tsep_c = None

        self.d_choke_mm = None
        self.ESP_freq = None
        self.p_intake_data_atm = None
        self.p_wellhead_data_atm = None
        self.p_buf_data_atm = None
        self.p_wf_atm = None
        self.cos_phi_data_d = None
        self.u_motor_data_v = None
        self.active_power_cs_data_kwt = None
        self.qliq_m3day = 100  # initial guess
        self.watercut_perc = None
        self.p_buf_data_atm = None
        self.c_calibr_head_d = 0.7  # initial guess
        self.c_calibr_power_d = 1.2  # initial guess

        self.result = None
        self.error_in_step = None
        self.p_buf_data_max_atm = None
        self.active_power_cs_data_max_kwt = None
        self.p_wellhead_data_max_atm = None
        self.qliq_max_m3day = None


def transfer_data_from_row_to_state(this_state, row_in_prepared_data, vfm_calc_option):
    """
    заполнение класса-состояния скважины с ЭЦН текущим набором входных данных (для данного момента времени)
    :param this_state: состояние скважины со всеми параметрами
    :param row_in_prepared_data: набора данных - строка входного DataFrame
    :param vfm_calc_option: флаг восстановления дебитов - если False - адаптация
    :return: заполненное состояние this_state
    """
    this_state.watercut_perc = row_in_prepared_data['Процент обводненности (СУ)']  # заполнение структуры данными
    this_state.rp_m3m3 = row_in_prepared_data['ГФ (СУ)']

    this_state.p_buf_data_atm = row_in_prepared_data['Рбуф (Ш)']
    #this_state.p_buf_data_atm = row_in_prepared_data['Линейное давление (СУ)'] * 10  # костыль
    #this_state.p_buf_data_atm = row_in_prepared_data['Рлин ТМ (Ш)']  # костыль

    # this_state.p_wellhead_data_atm = row_in_prepared_data['Рлин ТМ (Ш)']
    this_state.p_wellhead_data_atm = row_in_prepared_data['Линейное давление (СУ)'] * 10
    this_state.tsep_c = row_in_prepared_data['Температура на приеме насоса (пласт. жидкость) (СУ)']
    this_state.p_intake_data_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10
    this_state.psep_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10
    this_state.p_wf_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10
    this_state.d_choke_mm = row_in_prepared_data['Dшт (Ш)']
    this_state.ESP_freq = row_in_prepared_data['F вращ ТМ (Ш)']
    # this_state.ESP_freq = row_in_prepared_data['Выходная частота ПЧ (СУ)']
    this_state.active_power_cs_data_kwt = row_in_prepared_data['Активная мощность (СУ)'] * 1000
    this_state.u_motor_data_v = row_in_prepared_data['Напряжение на выходе ТМПН (СУ)']
    this_state.cos_phi_data_d = row_in_prepared_data['Коэффициент мощности (СУ)']
    if vfm_calc_option == True:
        this_state.c_calibr_head_d = row_in_prepared_data[
            "К. калибровки по напору - множитель (Модель) (Подготовленные)"]
        this_state.c_calibr_power_d = row_in_prepared_data[
            "К. калибровки по мощности - множитель (Модель) (Подготовленные)"]
    else:
        this_state.qliq_m3day = row_in_prepared_data['Объемный дебит жидкости (СУ)']
    return this_state


def get_fragmentation(length: int, slaves: int) -> list:
    """
    with length of jobs and amount of slaves returns list with turples.
    job_list[out[slave][0]: out[slave][1]] is a sub-list of jobs for this slave. slave \in [0, slaves-1]
    :param length: number of jobs
    :param slaves: amount of slaves
    :return: turples to distribute jobs
    """
    # defining step size
    step = int(length / slaves)
    # but int-like devision returns a bit less
    r = length - step * slaves
    # preparing out list with turples. r will be distributed over first slaves
    out = []
    cur_point = 0
    for i in range(slaves):
        if r > 0:
            # if we have non dealed r, push a piece
            out_el = (cur_point, cur_point + step + 1)
            r -= 1
        else:
            # if all the r already distributed then ok
            out_el = (cur_point, cur_point + step)
        cur_point = out_el[1]
        out.append(out_el)
    return out


def divide_prepared_data(prepared_data, options):  # TODO сделать разбивку с запасом - убрать потери точек
    """
    Разбивка всех исходных данных на равные части для реализации многопоточности
    :param prepared_data: подготовленные входные данные
    :param options: класс настроек расчета
    :return: определенная часть исходных данных, которая будет считаться данным потоком
    """
    fragmentation = get_fragmentation(prepared_data.shape[0], options.amount_of_threads)
    out = prepared_data[fragmentation[options.number_of_thread-1][0]: fragmentation[options.number_of_thread-1][1]]
    return out


def create_new_result_df(this_result, this_state, prepared_data, i):
    """
    Объединение всех результатов для данной итерации в один DataFrame
    :param this_result: список с результатами UniflocVBA
    :param this_state: класс-состояние скважины для данной итерации (входные данные)
    :param prepared_data: DataFrame входных данных
    :param i: номер строки в prepared_data для текущей итерации
    :return: new_dataframe - сводный результат расчета
    """
    new_dict = {}
    for j in range(len(this_result[1])):
        new_dict[this_result[1][j]] = [this_result[0][j]]
        print(str(this_result[1][j]) + " -  " + str(this_result[0][j]))
    new_dict['ГФ'] = [this_state.rp_m3m3]
    new_dict['Значение функции ошибки'] = [this_state.error_in_step]
    new_dict['Время'] = [prepared_data.index[i]]
    new_dataframe = pd.DataFrame(new_dict)
    new_dataframe.index = new_dataframe['Время']
    return new_dataframe
