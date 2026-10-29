from server import parse_csv, date_normal

def test():
    rows=b"Date,Description,Debit,Credit,Balance\n01/10/2026,Salary,,350000,350000\n02/10/2026,Supermarket,12500,,337500\n03/10/2026,Transfer to John,25000,,312500\n"
    tx,w=parse_csv(rows)
    assert len(tx)==3,tx
    assert [t["type"] for t in tx]==["income","expense","transfer"]
    assert sum(t["amount"] for t in tx if t["type"]=="expense")==12500
    assert date_normal("02/10/2026")=="2026-10-02"
    print("All parser smoke tests passed")
if __name__=="__main__":test()
