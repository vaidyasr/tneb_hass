# A Home Assistant custom component to get your TNEB Bill Amount, Units consumed and Due Date information.
To get started put all the files from/custom_components/tneb/ here: <config directory>/custom_components/tneb/

Example configuration.yaml:

```sensor:
  - platform: tneb
    consumerno: 1234567890 
    username: myusername
    password: mypassword
    scan_interval: 86400
