export type TxType = 'income' | 'expense' | 'transfer' | 'refund' | 'review';
export type Transaction = {
  id: string; date: string; description: string; amount: number;
  type: TxType; category: string; needsReview: boolean;
};
export type Report = {
  id: string; title: string; createdAt: string; source: string; isDemo: boolean;
  transactions: Transaction[]; periodStart: string; periodEnd: string;
};
export type Totals = { income: number; spending: number; transfers: number; refunds: number; remaining: number; grossOutflow: number };
