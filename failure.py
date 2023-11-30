import traceback
report = {}
for i in range(5):
    try:
        if i==2:
            a=1/0
        report[i]='SUCCESS'
    except Exception as e:
        report[i]='FAILED'
        print(str(e))
        traceback.print_exc()
        continue
for key,value in report.items():
        print(f"{key}: {value}")