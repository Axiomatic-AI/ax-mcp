## Case 1: Show All Available PDKs

### User Query
Show all available PDKs


### Tool Action
```
Called: list_available_pdks
Parameters: {}
```

Tool Response (Raw JSON)
```
{
  "pdks": [
    {
      "pdk_type": "cspdk.si220.cband",
      "description": "Cornerstone PDK on platform Si220 for C-band",
      "granted": true
    },
    {
      "pdk_type": "cspdk.si220.oband",
      "description": "Cornerstone PDK on platform Si220 for O-band",
      "granted": true
    },
    {
      "pdk_type": "amf.cband",
      "description": "AMF PDK for C-band",
      "granted": true
    },
    {
      "pdk_type": "amf.oband",
      "description": "AMF PDK for O-band",
      "granted": true
    }
```

### Final Rendered Response to User

Here are all the available PDKs that you have access to:

Available PDKs

1. cspdk.si220.cband
     - Description: Cornerstone PDK on platform Si220 for C-band
     - Status: ✅ Granted

2. cspdk.si220.oband
    - Description: Cornerstone PDK on platform Si220 for O-band
    - Status: ✅ Granted

3. amf.cband
    - Description: AMF PDK for C-band
    - Status: ✅ Granted

4. amf.oband
    - Description: AMF PDK for O-band
    - Status: ✅ Granted

You have access to 4 different PDKs covering both C-band and O-band wavelengths from two different providers:

- Cornerstone PDK (cspdk) on Si220 platform
- AMF PDK (amf)

All PDKs are currently granted and available for use in your photonic integrated circuit designs.

