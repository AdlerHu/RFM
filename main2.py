import pandas as pd
import numpy as np
import os


# 输入源数据文件名
def get_rfm(name='PYTHON-RFM实战数据.xlsx'):
    df = pd.read_excel(name)
    df = df.loc[df['订单状态'] == '交易成功', :]
    print('剔除退款后还剩:%d行' % len(df))
    df = df[['买家昵称', '付款日期', '实付金额']]

    r = df.groupby('买家昵称')['付款日期'].max().reset_index()
    r['R'] = (pd.to_datetime('2019-7-1') - r['付款日期']).dt.days
    r = r[['买家昵称', 'R']]

    # 引入日期标签辅助列
    df['日期标签'] = df['付款日期'].astype(str).str[:10]

    # 把单个用户一天内订单合并
    dup_f = df.groupby(['买家昵称', '日期标签'])['付款日期'].count().reset_index()

    # 对合并后的用户统计频次
    f = dup_f.groupby('买家昵称')['付款日期'].count().reset_index()
    f.columns = ['买家昵称', 'F']

    sum_m = df.groupby('买家昵称')['实付金额'].sum().reset_index()
    sum_m.columns = ['买家昵称', '总支付金额']
    com_m = pd.merge(sum_m, f, left_on='买家昵称', right_on='买家昵称', how='inner')

    # 计算用户平均支付金额
    com_m['M'] = com_m['总支付金额'] / com_m['F']

    rfm = pd.merge(r, com_m, left_on='买家昵称', right_on='买家昵称', how='inner')
    rfm = rfm[['买家昵称', 'R', 'F', 'M']]

    rfm['R-SCORE'] = pd.cut(rfm['R'], bins=[0, 30, 60, 90, 120, 1000000], labels=[5, 4, 3, 2, 1], right=False).astype(
        float)
    rfm['F-SCORE'] = pd.cut(rfm['F'], bins=[1, 2, 3, 4, 5, 1000000], labels=[1, 2, 3, 4, 5], right=False).astype(float)
    rfm['M-SCORE'] = pd.cut(rfm['M'], bins=[0, 50, 100, 150, 200, 1000000], labels=[1, 2, 3, 4, 5], right=False).astype(
        float)

    rfm['R是否大于均值'] = (rfm['R-SCORE'] > rfm['R-SCORE'].mean()) * 1
    rfm['F是否大于均值'] = (rfm['F-SCORE'] > rfm['F-SCORE'].mean()) * 1
    rfm['M是否大于均值'] = (rfm['M-SCORE'] > rfm['M-SCORE'].mean()) * 1

    rfm['人群数值'] = (rfm['R是否大于均值'] * 100) + (rfm['F是否大于均值'] * 10) + (rfm['M是否大于均值'] * 1)

    rfm['人群类型'] = rfm['人群数值'].apply(transform_label)

    count = rfm['人群类型'].value_counts().reset_index()
    count.columns = ['客户类型', '人数']
    count['人数占比'] = count['人数'] / count['人数'].sum()

    rfm['购买总金额'] = rfm['F'] * rfm['M']
    mon = rfm.groupby('人群类型')['购买总金额'].sum().reset_index()
    mon.columns = ['客户类型', '消费金额']
    mon['金额占比'] = mon['消费金额'] / mon['消费金额'].sum()

    result = pd.merge(count, mon, left_on='客户类型', right_on='客户类型')

    return result


# 判断R/F/M是否大于均值
def transform_label(x):
    if x == 111:
        label = '重要价值客户'
    elif x == 110:
        label = '消费潜力客户'
    elif x == 101:
        label = '频次深耕客户'
    elif x == 100:
        label = '新客户'
    elif x == 11:
        label = '重要价值流失预警客户'
    elif x == 10:
        label = '一般客户'
    elif x == 1:
        label = '高消费唤回客户'
    elif x == 0:
        label = '流失客户'
    return label


def main():
    res = get_rfm(name='PYTHON-RFM实战数据.xlsx')
    print(res)


if __name__ == '__main__':
    main()