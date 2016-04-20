#Gateway Monitor Application.
This is a python standalone package which record health status of device along with
internet connectivity history and POST this data to heroku web application every 10 sec.

### Deployment instructions


```bash
$ git clone https://github.com/sharadvishe/gateway_monitor.git
$ cd gateway_monitor
Change username and password in `get_api_token()` and save the file

$ zip -r ../gateway_monitor.zip *
```

Use this gateway_monitor.zip to deploy on the ConnectPort X2E device. 






