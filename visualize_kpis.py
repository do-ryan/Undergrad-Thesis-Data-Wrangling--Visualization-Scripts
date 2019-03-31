import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def stacked_barplot(df_stack_by_category, title, xlabels, ylabel, savename):
    '''
    :param DataFrame with columns as the stack, rows as the categories
    :return:
    '''

    indices = np.arange(df_stack_by_category.shape[1])
    WIDTH = 0.5

    cum_sum=0
    p = []
    for stack in df_stack_by_category.iterrows():
        p.append(plt.bar(x=indices, height=stack[1], bottom=cum_sum, width=WIDTH))
        cum_sum += stack[1]
    plt.title(title)
    plt.xticks(indices, xlabels)
    plt.ylabel(ylabel)
    plt.legend(p, df_stack_by_category.axes[0])
    plt.gcf().subplots_adjust(bottom=0.25, left=0.1)
    plt.ticklabel_format(style='sci', axis='y', scilimits=(-2,4))
    plt.savefig(savename)
    plt.close()
    return

def grouped_barplot(df_stack_by_category, title, xlabels, ylabel, spacing_factor, savename):
    '''
    :param DataFrame with columns as the stack, rows as the categories
    :return:
    '''

    indices = np.arange(df_stack_by_category.shape[1])*spacing_factor
    WIDTH = 0.5

    cum_spacing = 0
    p = []
    for stack in df_stack_by_category.iterrows():
        p.append(plt.bar(x=indices + cum_spacing, height=stack[1], bottom=0, width=WIDTH))
        cum_spacing += WIDTH

    plt.title(title)
    plt.xticks(indices + 0.5*WIDTH*(df_stack_by_category.shape[0]-1), xlabels, rotation=90, fontsize=10)
    plt.ylabel(ylabel)
    plt.legend(p, df_stack_by_category.axes[0])
    plt.gcf().subplots_adjust(bottom=0.25, left=0.2)
    plt.ticklabel_format(style='sci', axis='y', scilimits=(-2,4))
    plt.savefig(savename)
    plt.close()
    return

def main():

    kpi_throughput = pd.DataFrame.from_dict(np.load("kpi_throughput.npy").item())
    kpi_utilization = pd.DataFrame.from_dict(np.load("kpi_utilization.npy").item())
    kpi_cancellations = pd.DataFrame.from_dict(np.load("kpi_cancellations.npy").item())

    kpi_cost_components = pd.DataFrame.from_dict(np.load("kpi_cost_components.npy").item())
    for i, rows in kpi_cost_components.iterrows():
        for j, component in rows.iteritems():
            if type(component) is dict:
                kpi_cost_components.loc[i,j] = sum(component.values())

    kpi_total_cost = pd.DataFrame.from_dict(np.load("kpi_total_cost.npy").item())

    # COMPUTE DERIVED KPIS
    print("Total costs: ", kpi_total_cost.sum(axis=0))
    print("Average utilization: ", kpi_utilization.applymap(lambda x: abs(x)).mean(axis=0))
    print("Total cancellations: ", kpi_cancellations.sum(axis=0))
    print("Total throughput: ", kpi_throughput.sum(axis=0))

    stacked_barplot(kpi_total_cost, "Total Cost Comparison - Hospital Breakdown", ["Deterministic DORS", "Stochastic DORS"], "Total Cost over 15 day Planning Period (Dollars)", "kpi_total_cost")
    grouped_barplot(kpi_cost_components, "Total Cost Comparison - Component Breakdown", ["Surgical Suite\n Opening Cost", "OR Opening\n Cost", "Scheduling \nRevenue", "Waiting \nCost", "Cancellation \nCost"], "Total Cost(+) / Revenue(-) over \n15 day Planning Period (Dollars)", spacing_factor=1, savename="kpi_cost_components")
    stacked_barplot(kpi_throughput, "Patient Throughput Comparison - Hospital Breakdown", ["Deterministic DORS", "Stochastic DORS"], "Total Patient Throughput over Simulation Span (18 weeks)", "kpi_throughput")
    stacked_barplot(kpi_cancellations, "Patient Cancellations Comparison - Hospital Breakdown", ["Deterministic DORS", "Stochastic DORS"], "Total Patient Cancellations over Simulation Span (18 weeks)", "kpi_cancellations")
    grouped_barplot(kpi_utilization.applymap(lambda x: abs(x*100)), "OR Utilization Comparison - Hospital Breakdown", ["Deterministic\n DORS", "Stochastic\n DORS"], "OR Utilization (%) over Simulation Span (18 weeks)", spacing_factor=2, savename="kpi_utilization_breakdown")
    grouped_barplot(kpi_utilization.applymap(lambda x: abs(x*100)).mean(axis=0).to_frame(name="Average Utilization").transpose(), "Average OR Utilization Comparison",["Deterministic\n DORS", "Stochastic\n DORS"], "Average OR Utilization (%) over Simulation Span (18 weeks)", spacing_factor=1, savename="kpi_utilization")


    return

if __name__ == "__main__":
    main()