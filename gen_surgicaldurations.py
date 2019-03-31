import numpy as np
import math
import pandas as pd

def duration_sim(num_samples,num_patients,m_mu,m_sigma,m_lb,m_ub,m_file):
    m_li=[]

    mu = math.log(m_mu)- math.log(1+m_sigma**2/m_mu**2)/2
    sigma = math.sqrt(math.log(1+m_sigma**2/m_mu**2))
    for s in range(num_samples):
        li2 = []
        while (len(li2) < num_patients):
            temp = math.floor(np.random.lognormal(mu, sigma, 1)[0])
            if (temp >= m_lb and temp <= m_ub):
                li2.append(temp)
        m_li.append(li2)

    df = pd.DataFrame(m_li)
    df.T.to_csv(m_file, index=False)

def main():
    nS = 18
    nP = 12140
    duration_sim(nS, nP, 160, 40, 45, 480, m_file="surgical_durations.csv")
    return

if __name__ == "__main__":
    main()