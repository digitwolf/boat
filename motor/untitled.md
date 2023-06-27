# CanOPEN notes

Example Can message to read RPM
```
can1  040   [4]  CB F7 FF FF
```
This will read the TPDO #5 because 40 is the COB-ID

```
node.tpdo[5].clear()
node.tpdo[5].add_variable(0x2020,4)
node.tpdo[5].trans_type =1
node.tpdo[5].enabled = True
node.tpdo[5].cob_id = 64
node.tpdo.save()
```