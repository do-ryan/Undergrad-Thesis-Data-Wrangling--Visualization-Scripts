import numpy as np
import ast
import pandas as pd
import csv

def stringified_to_list(text_path, header):
    text = open(text_path, "r")
    in_list = False
    stringified_list = str("")

    for line in text:
        if len(line.split(": ")) > 1:
            if line.split(": ")[0] == header:
                in_list = True
                stringified_list += str(line.split(": ")[1])
            else:
                in_list = False
        elif in_list:
            stringified_list += line

    stringified_list = stringified_list.strip("\n") # final stringified nested list
    return ast.literal_eval(stringified_list)

def ydr_to_scheduleFunction(ydr, csv_path, open_duration, total_num_rooms):
    # takes in days by rooms opening schedule and returns (rooms*days) by hourly time schedule

    time_steps = np.arange(0, 24*60, 30) #24 hours, increments of 30 minutes
    open_time = 480//30 # 8 hours converted to increments of 30 minutes

    # initialization
    scheduleFunction = np.full((ydr.shape[0]*total_num_rooms, len(time_steps)), int(5)) # (days*rooms) x (number of time steps over a day)

    for i in range(ydr.shape[0]): # days
        for j in range (ydr.shape[1]): # rooms
            if ydr[i][j]:
                scheduleFunction[i*total_num_rooms+j][open_time:open_time+open_duration[i][j]//30] = int(1)

    np.savetxt(csv_path, scheduleFunction, delimiter = ",")
    return

def xhdpr_to_ArrivalTable(xhdpr, csv_path, start_time, run_time):
    # xhdpr: days x patients x rooms
    # writes day-wise patient arrival (in minutes)

    arrival_vector = []
    current_time = start_time

    while current_time <= start_time + run_time:
        for day in xhdpr:
            patient_count_day = np.count_nonzero(day == 1)
            for i in range(patient_count_day):
                arrival_vector.append(current_time)
            current_time += 60*24

    df = pd.DataFrame(arrival_vector, columns=["time"])
    df.to_csv(csv_path, index=False)

    return

def main():
    # HOSPITAL ORDER: (0) PMH, (1) TGH, (2) TWH
    stoch_yhdr = np.array(stringified_to_list("../ChengMaterial/March16/Sim-2ndDecomp_inst1007_nS5_BBD_nH3_nD15_nR5_nP100_iMac.txt", "yhdr"))
    det_yhdr = np.array(stringified_to_list("../ChengMaterial/March16/DORS+FFD_nH3_nD15_nR5_nP100_inst1007+_iMac_result.txt", "yhdr"))
    stoch_xhdpr = np.array(stringified_to_list("../ChengMaterial/March16/Sim-2ndDecomp_inst1007_nS5_BBD_nH3_nD15_nR5_nP100_iMac.txt", "xhdpr"))
    det_xhdpr = np.array(stringified_to_list("../ChengMaterial/March16/DORS+FFD_nH3_nD15_nR5_nP100_inst1007+_iMac_result.txt", "xhdpr"))

    # initialize scheduleFunction parameters
    nH = det_yhdr.shape[0]
    nD = det_yhdr.shape[1]
    nR = det_yhdr.shape[2]
    step_values = np.arange(420, 481, 30)
    openduration = np.random.choice(step_values, size=(nH, nD, nR))

    # Hospital 1
    ydr_to_scheduleFunction(ydr=stoch_yhdr[0], csv_path="PMH_stoch_raw_scheduleFunction.csv",
                            open_duration=openduration[0], total_num_rooms=22)
    ydr_to_scheduleFunction(ydr=det_yhdr[0], csv_path="PMH_det_raw_scheduleFunction.csv", open_duration=openduration[0],
                            total_num_rooms=22)
    xhdpr_to_ArrivalTable(xhdpr=stoch_xhdpr[0], csv_path="PMH_stoch_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)
    xhdpr_to_ArrivalTable(xhdpr=det_xhdpr[0], csv_path="PMH_det_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)
    # Hospital 2
    ydr_to_scheduleFunction(ydr=stoch_yhdr[1], csv_path="TGH_stoch_raw_scheduleFunction.csv",
                            open_duration=openduration[1], total_num_rooms=22)
    ydr_to_scheduleFunction(ydr=det_yhdr[1], csv_path="TGH_det_raw_scheduleFunction.csv", open_duration=openduration[1],
                            total_num_rooms=22)
    xhdpr_to_ArrivalTable(xhdpr=stoch_xhdpr[1], csv_path="TGH_stoch_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)
    xhdpr_to_ArrivalTable(xhdpr=det_xhdpr[1], csv_path="TGH_det_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)

    # Hospital 3
    ydr_to_scheduleFunction(ydr=stoch_yhdr[2], csv_path="TWH_stoch_raw_scheduleFunction.csv",
                            open_duration=openduration[2], total_num_rooms=22)
    ydr_to_scheduleFunction(ydr=det_yhdr[2], csv_path="TWH_det_raw_scheduleFunction.csv",
                            open_duration=openduration[2], total_num_rooms=22)
    xhdpr_to_ArrivalTable(xhdpr=stoch_xhdpr[2], csv_path="TWH_stoch_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)
    xhdpr_to_ArrivalTable(xhdpr=det_xhdpr[2], csv_path="TWH_det_raw_ArrivalTable.csv", start_time=100801,
                          run_time=182880)

    return

if __name__ == "__main__":
    main()