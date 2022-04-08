import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import pyplot
import numpy as np
from scipy.stats import shapiro
import scipy.stats as stats
from statsmodels.stats.proportion import proportions_ztest

# Data
Control_Group = pd.read_excel("ab_testing.xlsx", sheet_name='Control Group')  
Test_Group = pd.read_excel("ab_testing.xlsx", sheet_name='Test Group')

def check_df(dataframe, head=5):
    print("##################### Shape #####################")
    print(dataframe.shape)
    print("##################### Types #####################")
    print(dataframe.dtypes)
    print("##################### Head #####################")
    print(dataframe.head(head))
    print("##################### Tail #####################")
    print(dataframe.tail(head))
    print("##################### NA #####################")
    print(dataframe.isnull().sum())
    print("##################### Quantiles #####################")
    print(dataframe.quantile([0, 0.05, 0.50, 0.95, 0.99, 1]).T)

check_df(Control_Group)
check_df(Test_Group)


# Aykırı degerler icin esik degerin belirlenmesi
def outlier_thresholds(dataframe, variable, low_quantile=0.05, up_quantile=0.95):
    quantile_one = dataframe[variable].quantile(low_quantile)
    quantile_three = dataframe[variable].quantile(up_quantile)
    interquantile_range = quantile_three - quantile_one
    up_limit = quantile_three + 1.5 * interquantile_range
    low_limit = quantile_one - 1.5 * interquantile_range
    return low_limit, up_limit


# Aykırı deger var mi?
def has_outliers(dataframe, numeric_columns):
    for col in numeric_columns:
        low_limit, up_limit = outlier_thresholds(dataframe, col)
        if dataframe[(dataframe[col] > up_limit) | (dataframe[col] < low_limit)].any(axis=None):
            number_of_outliers = dataframe[(dataframe[col] > up_limit) | (dataframe[col] < low_limit)].shape[0]
            print(col, " : ", number_of_outliers, "outliers")

# Control Group 
for var in Control_Group:
    print(var, "has ", has_outliers(Control_Group, [var]), "Outliers")

# Test Group 
for var in Control_Group:
    print(var, "has ", has_outliers(Test_Group, [var]), "Outliers")


# kontrol ve test grubunun birleştirilmesi
Control_Group["Group"] = "A"  # Maximum Bidding
Test_Group["Group"] = "B"  # Average Bidding


AB = Control_Group.append(Test_Group)
AB.tail()

"""
AB testi icin AB isminde yeni dataframe olusturulmustur
- Control değişkeni -> Kontrol grubu Purchase degerleri
- Test değişkeni -> Test grubu Purchase degerleri 
"""

AB.shape

# Kontrol ve Test gruplarının purchase ortalamaları  #median?
print(" Mean of purchase of control group(A): %.3f" % AB[AB["Group"] == "A"]["Purchase"].mean(), "\n",
      "Mean of purchase of test group(B): %.3f" % AB[AB["Group"] == "B"]["Purchase"].mean())

print(" Median of purchase of control group(A): %.3f" % AB[AB["Group"] == "A"]["Purchase"].median(), "\n",
      " Median of purchase of test group(B): %.3f" % AB[AB["Group"] == "B"]["Purchase"].median())


"""
İki yöntemin ortalama değerlerine bakıldığında aralarındaki farklılık olduğu görülmektedir.
Ortalama satın alma değeri test grubu(B) lehinedir.
"""



## Cikan test sonuclarinin istatistiksel olarak anlamli olup olmadıginin yorumlanmasi

def AB_Test(dataframe, group, target):
    # A ve B gruplarının ayrılması
    groupA = dataframe[dataframe[group] == "A"][target]  #current
    groupB = dataframe[dataframe[group] == "B"][target]  #new

    # Varsayım: Normallik
    # Shapiro-Wilks Test
    # H0: Örnek dağılımı ile teorik normal dağılım arasında istatistiksel olarak anlamlı bir fark yoktur! -False
    # H1: Örnek dağılımı ile teorik normal dağılım arasında istatistiksel olarak anlamlı bir fark vardır! -True
    # p-value 0.05 den küçük ise H0 reddedilir.
    ntA = shapiro(groupA)[1] < 0.05
    ntB = shapiro(groupB)[1] < 0.05

    if (ntA == False) & (ntB == False):  # "H0: Normal dağılım" sağlandıysa
        # Parametric Test
        # Varsayım: Varyans Homojenliği
        leveneTest = stats.levene(groupA, groupB)[1] < 0.05
        # H0: karşılaştırılan gruplar eşit varyansa sahiptir. - False
        # H1: karşılaştırılan gruplar eşit varyansa sahip değildir. - Ture
        if leveneTest == False:  # eşit varyansa sahiplerse
            # Homogeneity
            ttest = stats.ttest_ind(groupA, groupB, equal_var=True)[1]
            # H0: M1 == M2 - False
            # H1: M1 != M2 - True
        else:  # eşit varyansa sahip değillerse  welch
            # Heterogeneous
            ttest = stats.ttest_ind(groupA, groupB, equal_var=False)[1]
            # H0: M1 == M2 - False
            # H1: M1 != M2 - True
    else:  # Normal dağılıma sahip değilse
        # Non-Parametric Test
        ttest = stats.mannwhitneyu(groupA, groupB)[1]
        # H0: M1 == M2 - False
        # H1: M1 != M2 - True

    # Sonuc
    temp = pd.DataFrame({"AB Hypothesis": [ttest < 0.05], "p-value": [ttest]})
    temp["Test Type"] = np.where((ntA == False) & (ntB == False), "Parametric", "Non-Parametric")
    temp["AB Hypothesis"] = np.where(temp["AB Hypothesis"] == False, "Fail to Reject H0", "Reject H0")
    temp["Comment"] = np.where(temp["AB Hypothesis"] == "Fail to Reject H0", "A/B groups are similar!",
                               "A/B groups are not similar!")

    if (ntA == False) & (ntB == False):
        temp["Homogeneity"] = np.where(leveneTest == False, "Yes", "No")
        temp = temp[["Test Type", "Homogeneity", "AB Hypothesis", "p-value", "Comment"]]
    else:
        temp = temp[["Test Type", "AB Hypothesis", "p-value", "Comment"]]

    return temp

AB_Test(AB, group="Group", target="Purchase")

"""
Kontrol grubu (A) ile Test grubu (B) arasında istatistiksel olarak anlamlı farklılık yoktur.
"""


#######################################
"""Website Click Through Rate (CTR)

-->Reklamı GÖREN kullanıcıların, reklamı ne sıklıkta TIKLADIKLARINI gösteren orandır.
-->Reklam Tıklanma Sayısı/ Reklam Gösterilme Sayısı
-->Örnek 5 tıklama, 100 gösterimde CTR= %5"""


AB.head()

control_CTR = AB.loc[AB["Group"] == "A", "Click"].sum() / AB.loc[AB["Group"] == "A", "Impression"].sum()
test_CTR = AB.loc[AB["Group"] == "B", "Click"].sum() / AB.loc[AB["Group"] == "B", "Impression"].sum()
print("Control_CTR: ", control_CTR, "\n", "test_CTR: ", test_CTR)

# İlk bakışta tıklama oranının kontrol grubu lehine olduğunu görüyoruz.
# Yani reklamı görüp de tıklayanların oranı mevcut sistemde daha iyi gibi görünüyor.

"""
Varsayım: n≥ 30 sağlandı.
Hipotezler
H0: Deneyin kullanıcı davranışına istatistiksel olarak anlamlı etkisi yoktur. (p_cont = p_test)
H1: Deneyin kullanıcı davranışına istatistiksel olarak anlamlı etkisi vardır. (p_cont ≠ p_test)
"""


click_count= AB.loc[AB["Group"] == "B", "Click"].sum() ,  AB.loc[AB["Group"] == "A", "Click"].sum()
impression_count= AB.loc[AB["Group"] == "B", "Impression"].sum(), AB.loc[AB["Group"] == "A", "Impression"].sum()
proportions_ztest(count=click_count, nobs=impression_count)
