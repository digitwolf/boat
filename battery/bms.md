# Explanation of CAN protocol for Thunderstruck BMS
## DD_BMS_STATUS_IND
This message is sent once a second by the BMS to indicate BMS health.
```DD_BMS_STATUS_IND 0x01dd0001```


```
// Dilithium Design CAN Message Definitions
#if 0
#define byte unsigned char; // 8 bits
#define word unsigned int; // 16 bits
#endif
//
// DD_BMS_STATUS_IND
//
// This message is sent once a second by the BMS to indicate BMS health.
//
#define DD_BMS_STATUS_IND 0x01dd0001
// BMS status flag definitions
#define BMS_FLAG_CELL_HVC 0x01 // at least one cell v is >HVC
#define BMS_FLAG_CELL_LVC 0x02 // at least one cell v is <LVC
#define BMS_FLAG_CELL_BVC 0x04 // at least one cell v is >BVC
// BMS flag definitions
#define BMS_FAULT_NOT_LOCKED 0x01 // configuration not locked
#define BMS_FAULT_CENSUS 0x02 // not all cells present
#define BMS_FAULT_OVERTEMP 0x04 // thermistor overtemp
#define BMS_FAULT_THERM_CENSUS 0x08 // not all thermistors present
typedef struct tDD_BMS_StatusInd
{
byte bBmsStatusFlags;
byte bBmscId; // bmsc id (0..3)
byte bBmscFault;
byte bLtcFault; // bit mask; 1 indicates error
byte bLtcCount; // number of LTCs
} tDD_BMS_StatusInd;
//
```

## DD_BMSC_TH_STATUS_IND
This message is sent once a second sent by the BMS to report the
thermistor temperatures. Each report is for one LTC, and so it takes
8 seconds to report the temperatures of all thermistors
LTCs are numbered from 0 to 7; `bLtcIdx` indicates the LTC

Each LTC supports 5 thermistors, numbered 1 to 5
`bThEnabled` is a bitmask that indicates which thermistors are enabled
`bThPresent` is a bitmask that indicates which thermistors are detected
`bThTempInC` is an array of 5 entries that contains the temperature, in C, for each thermistor
```
//

//
#define DD_BMSC_TH_STATUS_IND 0x01df0e00
#define DD_BMSC2_TH_STATUS_IND 0x01df0e10
#define DD_BMSC3_TH_STATUS_IND 0x01df0e20
#define DD_BMSC4_TH_STATUS_IND 0x01df0e30
typedef struct tDD_BMSCThStatus
{
Battery Management System v2.2 July 2019
-43-
byte bLtcIdx; // 0 .. 7
byte bThEnabled; // bitmask – 0b000xxxxx
byte bThPresent; // bitmask – 0b000xxxxx
byte bThTemp[5]; // in Centigrade
} tDD_BMSCThStatus;
//
// DD_BMS_CVCUR_REQ
// DD_BMS_CVCUR_C1_TO_C4_RSP
// DD_BMS_CVCUR_C5_TO_C8_RSP
// DD_BMS_CVCUR_C9_TO_C12_RSP
//
// These messages report Current Cell Cell data from the BMSs
//
// The message ID is of the form 0xppppggbl
//
// pppp = 01de - message prefix
//
// gg = 08 – request
// = 09 – reply, cells 1 to 4
// = 0a – reply, cells 5 to 8
// = 0b – reply, cells 9 to 12
//
// b = 0 to 3 (for bmsc 1 to 4)
//
// l = 0 to 7 (for LTC 1 to 8)
//
// Example: To request the cell voltage data for bmsc1:ltc3,
// the <bmsc id> is 0 and the <ltc id> is 2.
// The following id must be sent:
//
// 0x01de0802
//
// The BMSC will then reply with three CAN messages with the following ids
//
// 0x01df0902
// 0x01df0a02
// 0x01df0b02
//
// The reply message will have a payload using the structure tDD_BMS_RawData,
// which contains four cell voltage values
//
#define DD_BMS_CVCUR_REQ 0x01de0800
#define DD_BMS_CVCUR_C1_TO_C4_RSP 0x01df0900
#define DD_BMS_CVCUR_C5_TO_C8_RSP 0x01df0a00
#define DD_BMS_CVCUR_C9_TO_C12_RSP 0x01df0b00
#define DD_BMSC_MASK 0x0030 // 2 bits of bmsc idx (0 – 3)
#define DD_LTC_MASK 0x0007 // 3 bits of ltc idx (0 – 7)
// tDD_BMS_RawData
typedef struct tDD_BMS_RawData
{
word wData[4]; // cell voltages in tenths of mv
} tDD_BMS_RawData;
```