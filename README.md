# ezprinting
Python package to easily submit print jobs to a printer configured on either a CUPS server or Google Cloud Print.

GCP printing is achieved using **service account authentication** which is the best authentication method provided by Google for server-to-server interactions. This means you will need to download a **service_account.json** file from Google. 

We plan to support other authentication means in the future (i.e. refresh tokens).

## Installation ##
pip install ezprinting
or
poetry add ezpriting

pyCups is a dependency which needs libcups2-dev (this is the name on Ubuntu/Debian) to be installed (sudo apt install libcups2-dev).

## Quick Start Guide ##

**Note:** success=True/False in the examples below indicate whether or not the print job was successfully submitted to CUPS or GCP, not that it was successfully printed.

### 1. Option one:
```
from ezprinting import PrintJob
    
with open('service_account.json', 'rb') as f:
    service_account = f.read()

with open('dummy.pdf', 'rb') as f:
    content = f.read()

# If we want to print to GCP...
pjob = PrintJob.new_gcp(service_account=service_account, printer_id='gcp-printer-id', content=content)
success = pjob.print()

# If we want to use CUPS instead...
pjob = PrintJob.new_cups(printer_name='cups-printer-name', content=content)
success = pjob.print()

# Use host="cups.domain.tld:631", username="lpadmin", password="123456" to specify
# a remote cups server with authentication.
# By default "localhost:631" is assumed with blank user/passwd


```

If **content** is in PDF there is no need to specify content_type. Auto detection of content-type is not available yet, if you skip content_type than "application/pdf" is assumed.


### 2. Option two:
```
from ezprinting import PrintServer, Printer, PrintJob
import json

with open('service_account.json', 'rb') as f:
    service_account = f.read()

with open('dummy.pdf', 'rb') as f:
    content = f.read()

# If we want GCP...
print_server = PrintServer.gcp(service_account=service_account)

# If we want CUPS on localhost...
print_server = PrintServer.cups()
# If we want remote CUPS server...
print_server = PrintServer.cups(host="cups.domain.tld:631", username="lpadmin", password="123456")

# the rest of the code is the same for either cups or GCP...

connection_ok, message = print_server.test_connection()
print("Testing connection: {} - {}".format(connection_ok, message))

# Let's check what printers we have available
if connection_ok:
    printers = print_server.get_printers()
    print(json.dumps(printers, sort_keys=True, indent=4))
    printer = Printer(print_server, 'printer name (CUPS) or printer ID (GCP)')
    printer_exists = printer.check_printer_exists() 
    print("Does the printer exist on that print server? {}".format(printer_exists))
    if printer_exists:
        pjob = PrintJob(printer=printer, content=content)
        success = pjob.print()
        print('Print job submitted with success? {}'.format(success))
        if success:
            print('Print job id: {}'.format(pjob.job_id))
```

## Testing

You can easily test the functionality of this package by making use of the built in test code.

To test GCP functionality you need to add a **service_account.json** (download that from Google) to the *tests/private_data/* directory.

To test CUPS functionality you must have a valid *tests/private_data/cups.json*.

To define the documents you want to test print and the printers where those documents should be test printed you must have the files:
* tests/private_data/printers.json
* tests/data/print_tests.json

Commented sample json files are provided (do not forget to delete the comments, JSON does not support comments).

## State of this package
The code in this repository is being used in production and mostly works. However, it is very new and does not handle well exceptional cases.
A large piece that is still missing is functionality on the PrintJob class to track the lifecylce of a print job and being able to figure out what went wrong when something goes wrong (e.g. paper jam, out of paper, out of ink, etc).
Your help is welcome to fill in the gaps. And please, do file bug reports.

## Main TO-DOs
* [ ] Support GCP authentication with refresh token;
* [ ] Add a Printer.search_by_serial_number() function to search printer name or id by serial number (GCP printer ids are somewhat volatile);
* [ ] Develop functionality on the PrintJob class to track the state of a print job and identify causes of failure (e.g. jam, out of paper, out of ink, etc)  
* [ ] Enable printing directly to IPP printers;
* [ ] Add-on: mqtt monitor to send print jobs received on mqtt topics, with full QoS implementation; 

**Feel free to help fill-in the gaps!**

## Motivation
Having remote web applications automatically print to local printers can be difficult. However, this is often a necessity.

The task I had at hand was to have a web-based ERP software automatically push print jobs to various printers on any organization. Before, users would click a "Print" button that would open a new tab on the user's browser with the PDF content displayed and again a "Print" button to actually print. While this workflow works, it adds a few more seconds and an additional click to what could be a one-click operation. Also, in some cases we wanted the printer to kick-off the action (i.e. automatically print shelf labels when a product price has changed, automatically print the picking list for a warehouse operator, etc).

#### When describing the problem, we figured that:
1. We needed to standardize "the other side". Dealing with printer models, drivers, device discovery, etc was way out of scope and we did not need to reinvent the wheel;
2. We needed remote access to those printers with little or no configuration of the network on the remote site (even setting port forwarding can be a challenge to some customers);
3. We needed a solution that our clients could handle themselves with little to no support.

#### In the end, we decided that:
1. Google Cloud Print is the easiest solution that any customer could handle and would work everywhere. However, not all printers support GCP;
2. If the customer wants to suport other kinds of printers (like 80mm thermal receipt printers, Brother's line of QL label printers,  and even legacy equipment), he could do so by configuring everything on a dedicated CUPS (virtual) server;
3. Going CUPS does not mean abandoning GCP. With the official [Google Cloud Print Connector](https://github.com/google/cloud-print-connector), all printers on a CUPS server will be kept sincronized with GCP.

#### When testing our solution, we found out that:
1. Setting up a CUPS servers to support any number of printers is easy, most printer manufacturers have official CUPS drivers and installing printers on CUPS is often faster than on any other solution (even Windows);
2. Lots of clients have network-ready printers connected via USB. Having our clients move all those devices to plug directly to the network was the most difficult part;
3. To avoid headaches, network printers should have static IP addresses which is what CUPS should point to. Do not rely on DNSSD or any other kind of discovery protocol.
4. With a CUPS server and the [Google Cloud Print coonnector](https://github.com/google/cloud-print-connector) we had at least a few options to remotely access printers on a remote site (pure GCP, port 631 forwarding, ssh tunnel, VPN, etc) which is exactly what a web-based software hosted on the cloud needs;
5. The missing piece of the puzzle was a python package to let us easily submit print jobs to those remote printers, and this is what this package tries to accomplish.

## Other (random) notes
* pycups <=1.9.73 has a bug that prevents CUPS from working. You will see a filter failed or some kind of "document corrupted" message;
* The Google Cloud Connector will keep all of your CUPS printers in sync with a Google Cloud Print account. However, the
printer ids are not persistent, they may change if you make some changes to your CUPS printers (and do not have enough 
experience to say when/why these ids change, but they may change). In the future we plan to support setting printer by 
serial number;
* The service account (SA) comes with a virtual email. You must either share your printers with the email of your service 
account or share the printers with a Google Group which contains your service account email address as a group member. 
The Google Cloud Print Connector has a "share_scope" parameter which accepts only one email address and should be the 
address of the Google group. However, this method did not wrk well for us so we simply share the printers with the SA email;
* When a printer is shared with the SA email, it must be accepted first. There is an undocumented API call "/processInvite"
which is the only way to accept it for a SA email. This package supports this call in the Printer.enable_printer() method. 
Also, for GCP the function Printer.check_printer_exists() processes the invite if the first query for the printer id returns
nothing;  
