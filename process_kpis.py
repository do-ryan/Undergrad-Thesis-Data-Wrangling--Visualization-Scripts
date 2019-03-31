import csv
import fnmatch as fm
import numpy as np
import output_to_schedule

def readTsv(tsv_path):
    '''
    :param tsv_path: file path to tsv
    :return: nested list of kpi's: first column: kpi, 3rd column: value
    '''
    with open(tsv_path) as f:
        reader = csv.reader(f, delimiter="\t")
        d = list(reader)
    return d

def parseThroughput(det_kpi_dict, stoch_kpi_dict):
    '''
    :param det_kpi_dict: {"model deterministic version": nested list of kpis, values}
    :param stoch_kpi_dict: {"model stochastic version": nested list of kpis, values}
    :return: dictionary: {"det":{"model": throughput}}
    '''
    kpi_throughput={"det":{},"stoch":{}}
    for modelkpis in det_kpi_dict.items():
        total_throughput = 0
        for item in modelkpis[1]:
            if item[0]=="SS_O:Throughput by Service" and fm.fnmatch(item[1], "*Surgery Throughput"):
                total_throughput += int(item[len(item)-1])
        kpi_throughput["det"][modelkpis[0]]=total_throughput

    for modelkpis in stoch_kpi_dict.items():
        total_throughput = 0
        for item in modelkpis[1]:
            if item[0]=="SS_O:Throughput by Service" and fm.fnmatch(item[1], "*Surgery Throughput"):
                total_throughput += int(item[len(item)-1])
        kpi_throughput["stoch"][modelkpis[0]]=total_throughput

    return kpi_throughput

def parseCancellations(det_kpi_dict, stoch_kpi_dict):
    '''
    :param det_kpi_dict: {"model deterministic version": nested list of kpis, values}
    :param stoch_kpi_dict: {"model stochastic version": nested list of kpis, values}
    :return: dictionary: {"det":{"model": cancellations}}
    '''
    kpi_cancellations={"det":{},"stoch":{}}
    for modelkpis in det_kpi_dict.items():
        total_cancellations = 0
        for item in modelkpis[1]:
            if item[0]=="SS_O:Cancellations by Service":
                total_cancellations += int(item[len(item)-1])
        kpi_cancellations["det"][modelkpis[0]]=total_cancellations

    for modelkpis in stoch_kpi_dict.items():
        total_cancellations = 0
        for item in modelkpis[1]:
            if item[0]=="SS_O:Cancellations by Service":
                total_cancellations += int(item[len(item)-1])
        kpi_cancellations["stoch"][modelkpis[0]]=total_cancellations

    return kpi_cancellations

def parseUtilization(det_kpi_dict, stoch_kpi_dict):
    '''
    :param det_kpi_dict: {"model deterministic version": nested list of kpis, values}
    :param stoch_kpi_dict: {"model stochastic version": nested list of kpis, values}
    :return: dictionary: {"det":{"model": utilization}}
    '''
    kpi_utilization = {"det": {}, "stoch": {}}
    for modelkpis in det_kpi_dict.items():
        utilization = []
        for item in modelkpis[1]:
            if item[0]=="SS_O:OR Utilization" and fm.fnmatch(item[1], "*Adjusted Total OR Utilization") and float(item[len(item)-1]) != 0:
                utilization.append(float(item[len(item)-1]))
        kpi_utilization["det"][modelkpis[0]]= sum(utilization)/len(utilization)

    for modelkpis in stoch_kpi_dict.items():
        utilization = []
        for item in modelkpis[1]:
            if item[0]=="SS_O:OR Utilization" and fm.fnmatch(item[1], "*Adjusted Total OR Utilization") and float(item[len(item)-1]) != 0:
                utilization.append(float(item[len(item)-1]))
        kpi_utilization["stoch"][modelkpis[0]]= sum(utilization)/len(utilization)

    return kpi_utilization

def computeTotalCost(kpi_cancellations, sim_time, plan_horizon, opening_schedules):
    '''
    :param kpi_cancellations: {"det":{"model": cancellations}}
    :param sim_time: in minutes, 18 weeks
    :param plan_horizon: in minutes, 15 days
    :param opening_schedules: patient-hospital-or-day assignments, OR/hospital opening schedules
    :return: cost dictionary of each component, total cost
    '''
    G = [1500, 2500]
    F = [4000, 6000]
    alpha_p = [60, 120] #days elapsed since referral date of patient
    rho_p = [1, 5] #patient urgency score
    kappa_1 = 50 #dollar cost
    kappa_2 = -5  # dollar cost
    kappa_3 = -80 # cancellation cost coefficient
    num_patients = opening_schedules["det"]["xhdpr"].shape[2]
    num_days = opening_schedules["det"]["xhdpr"].shape[1]
    cost_dict = {}

    #hospital opening cost
    cost_dict["hospital_opening_cost"] = {"det":{}, "stoch":{}}
    for scheds in opening_schedules.items():
        for i, hospital_sched in enumerate(scheds[1]["uhd"]):
            cost_dict["hospital_opening_cost"][scheds[0]]["hospital" + str(i+1)] = np.sum(np.random.uniform(low=G[0], high=G[1], size=(np.count_nonzero(hospital_sched))))

    #OR opening cost
    cost_dict["or_opening_cost"] = {"det": {}, "stoch": {}}
    for scheds in opening_schedules.items():
        for i, or_sched in enumerate(scheds[1]["yhdr"]):
            cost_dict["or_opening_cost"][scheds[0]]["hospital" + str(i + 1)] = np.sum(np.random.uniform(low=F[0], high=F[1], size=(np.count_nonzero(or_sched))))

    #scheduling revenue
    cost_dict["sched_revenue"] = {"det": {}, "stoch": {}}
    for scheds in opening_schedules.items(): #det and stoch
        for i, patient_sched in enumerate(scheds[1]["xhdpr"]): # for each hospital
            day_sched_rev = 0
            for d, day in enumerate(patient_sched): # for every patient assignment (patient x OR) per day
                rho = np.random.randint(low=rho_p[0], high=rho_p[1], size=np.count_nonzero(day))
                alpha = np.random.uniform(low=alpha_p[0], high=alpha_p[1], size=np.count_nonzero(day))
                patient_sched_rev=kappa_1*np.multiply(rho,((d+1) - alpha))
                day_sched_rev += np.sum(patient_sched_rev)
            cost_dict["sched_revenue"][scheds[0]]["hospital" + str(i+1)] = day_sched_rev

    #waiting cost
    cost_dict["waiting_cost"] = {"det": {}, "stoch": {}}
    for scheds in opening_schedules.items():  # det and stoch
            num_scheduled = np.count_nonzero(scheds[1]["xhdpr"])
            rho = np.random.randint(low=rho_p[0], high=rho_p[1], size=num_patients - num_scheduled)
            alpha = np.random.uniform(low=alpha_p[0], high=alpha_p[1], size=num_patients - num_scheduled)
            cost_dict["waiting_cost"][scheds[0]] = kappa_2 * np.sum(np.multiply(rho, (num_days+1 - alpha)))

    #cancellation cost
    cost_dict["cancellation_cost"] = {"det": {}, "stoch": {}}
    for item in kpi_cancellations.items(): # det and stoch
        for i, hospital_cancellations in enumerate(item[1].items()): # for each hospital
            rho = np.random.randint(low=rho_p[0], high=rho_p[1], size=hospital_cancellations[1])
            alpha = np.random.uniform(low=alpha_p[0], high=alpha_p[1], size=hospital_cancellations[1])
            cost_dict["cancellation_cost"][item[0]][hospital_cancellations[0]] = kappa_3 * np.sum(np.multiply(rho, (num_days+1 - alpha))) * (plan_horizon/sim_time) # scale down

    #total up components for each model
    cost_dict_totals = {"det": {}, "stoch": {}}
    for component in cost_dict.values(): #for every cost component
        for scenario in component.items(): #for det and stoch
            if type(scenario[1]) is dict:
                for hospital in scenario[1].items(): # for every model's cost component
                    if hospital[0] in cost_dict_totals[scenario[0]]:
                        cost_dict_totals[scenario[0]][hospital[0]] += hospital[1]
                    else:
                        cost_dict_totals[scenario[0]][hospital[0]] = hospital[1]
            elif type(scenario[1]) is float:
                for hospital in cost_dict_totals[scenario[0]].items(): #assuming each hospital (model)'s total cost has been initialized
                    hospital[1] += scenario[1]

    return cost_dict, cost_dict_totals

def dict_to_nparray(dict):
    """
    :param dict:
    :return:
    """

    return

def main():
    det_kpi_dict = {}
    stoch_kpi_dict = {}
    det_kpi_dict["hospital1"] = readTsv("pmh_det_kpis.txt")
    stoch_kpi_dict["hospital1"] = readTsv("pmh_stoch_kpis_cut_openings_after_5_days.txt")
    det_kpi_dict["hospital2"] = readTsv("tgh_det_kpis.txt")
    stoch_kpi_dict["hospital2"] = readTsv("tgh_stoch_kpis.txt")
    det_kpi_dict["hospital3"] = readTsv("twh_det_kpis.txt")
    stoch_kpi_dict["hospital3"] = readTsv("twh_stoch_kpis.txt")

    kpi_throughput = parseThroughput(det_kpi_dict, stoch_kpi_dict)
    kpi_utilization = parseUtilization(det_kpi_dict, stoch_kpi_dict)
    kpi_cancellations = parseCancellations(det_kpi_dict, stoch_kpi_dict)

    stoch_yhdr = np.array(output_to_schedule.stringified_to_list("../ChengMaterial/March16/Sim-2ndDecomp_inst1007_nS5_BBD_nH3_nD15_nR5_nP100_iMac.txt", "yhdr"))
    det_yhdr = np.array(output_to_schedule.stringified_to_list("../ChengMaterial/March16/DORS+FFD_nH3_nD15_nR5_nP100_inst1007+_iMac_result.txt", "yhdr"))
    stoch_uhd = np.array(output_to_schedule.stringified_to_list("../ChengMaterial/March16/Sim-2ndDecomp_inst1007_nS5_BBD_nH3_nD15_nR5_nP100_iMac.txt", "uhd"))
    det_uhd = np.array(output_to_schedule.stringified_to_list("../ChengMaterial/March16/DORS+FFD_nH3_nD15_nR5_nP100_inst1007+_iMac_result.txt", "uhd"))
    stoch_xhdpr = np.array(output_to_schedule.stringified_to_list("../ChengMaterial/March16/Sim-2ndDecomp_inst1007_nS5_BBD_nH3_nD15_nR5_nP100_iMac.txt", "xhdpr"))
    det_xhdpr = np.array(output_to_schedule.stringified_to_list( "../ChengMaterial/March16/DORS+FFD_nH3_nD15_nR5_nP100_inst1007+_iMac_result.txt", "xhdpr"))
    opening_schedules = {"det":{"yhdr": det_yhdr, "uhd": det_uhd, "xhdpr": det_xhdpr}, "stoch":{"yhdr": stoch_yhdr, "uhd": stoch_uhd, "xhdpr": stoch_xhdpr}}

    kpi_cost_components, kpi_total_cost = computeTotalCost(kpi_cancellations, sim_time=182880, plan_horizon=21600, opening_schedules=opening_schedules)

    np.save("kpi_throughput.npy", kpi_throughput)
    np.save("kpi_utilization.npy", kpi_utilization)
    np.save("kpi_cancellations.npy", kpi_cancellations)
    np.save("kpi_cost_components.npy", kpi_cost_components)
    np.save("kpi_total_cost.npy", kpi_total_cost)

    return

if __name__ == "__main__":
    main()
