# Redeam API Test

```
usage: get-availability -pid PRODUCTID -sid SUPPLIERID [-sdate [STARTDATE]]
                        [-edate [ENDDATE]] [-h]

Utilizes Redeam API to obtain availability for specified products. If no date
arguments are specified, search will default to two weeks out from today's
date.

required arguments:
  -pid PRODUCTID, --productid PRODUCTID
                        for testing, use: 02f0c6cb-77ae-4fcc-8f4d-99bc0c3bee18
  -sid SUPPLIERID, --supplierid SUPPLIERID
                        for testing, use: fc49b925-6942-4df8-954b-ed7df10adf7e

optional arguments:
  -sdate [STARTDATE], --startdate [STARTDATE]
                        YYYY-MM-DD formatting. Defaults to today's date
  -edate [ENDDATE], --enddate [ENDDATE]
                        YYYY-MM-DD formatting. Defaults to two weeks from
                        today's date
  -h, --help            show this help message and exit
```

Please note that you need to add API credentials to config.ini.template, and rename to `config.ini`
