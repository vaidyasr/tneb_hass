"""Support for TNEB Bill Payment Gateway.

configuration.yaml

sensor:
  - platform: tneb
    name: "My 1st onnection"
    consumerno: 1234567890
    username: xxyyzz123
    password: yourpassword
    scan_interval: 3600
"""
from datetime import timedelta
import requests,json,untangle,logging,codecs
import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_RESOURCES
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.tnebnet.org"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=3600)
DEFAULT_NAME = "TNEB Consumer"

SENSOR_PREFIX = 'tneb_'
SENSOR_TYPES = {
    'consumerName': ['Consumer Name', 'mdi:account'],
    'phase': ['Phase', 'mdi:numeric'],
    'meterNumber': ['Meter Number', 'mdi:numeric'],
    'readingDate': ['Reading Date',  'mdi:calender'],
    'meterReading': ['Meter Reading',  'mdi:card-text-outline'],
    'usedUnits': ['Used Units', 'mdi:counter'],
    'ccCharges': ['CC Charges',  'mdi:cash-100'],
    'otherCharges': ['Other Charges',  'mdi:cash-100'],
    'billAmount': ['Bill Amount',  'mdi:cash-100'],
    'totalAmount': ['Total Amount',  'mdi:cash-100'],
    'dueDate': ['Due Date',  'mdi:calender'],
    'billPaidAmount': ['Bill Paid Amount',  'mdi:cash-100'],
    'receiptNumber': ['Receipt Number',  'mdi:numeric'],
    'paymentDate': ['Payment Date', 'mdi:calender']
}

CONF_CONSUMERNO = "consumerno"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CONSUMERNO): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_RESOURCES, default=[]):
            vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)])
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the TNEB bill sensor."""
    consumer_no = config.get(CONF_CONSUMERNO)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    try:
        data = TNEBBillData(consumer_no, username, password)
    except RunTimeError:
        _LOGGER.error("Unable to connect to TNEB Portal %s:%s",
                      BASE_URL)
        return False

    entities = []
    entities.append(TNEBBillSensor(data, "consumerNo", consumer_no))
    entities.append(TNEBBillSensor(data, "consumerName", consumer_no))
    entities.append(TNEBBillSensor(data, "phase", consumer_no))
    entities.append(TNEBBillSensor(data, "meterNumber", consumer_no))
    entities.append(TNEBBillSensor(data, "readingDate", consumer_no))
    entities.append(TNEBBillSensor(data, "meterReading", consumer_no))
    entities.append(TNEBBillSensor(data, "usedUnits", consumer_no))
    entities.append(TNEBBillSensor(data, "ccCharges", consumer_no))
    entities.append(TNEBBillSensor(data, "otherCharges", consumer_no))
    entities.append(TNEBBillSensor(data, "billAmount", consumer_no))
    entities.append(TNEBBillSensor(data, "totalAmount", consumer_no))
    entities.append(TNEBBillSensor(data, "dueDate", consumer_no))
    entities.append(TNEBBillSensor(data, "billPaidAmount", consumer_no))
    entities.append(TNEBBillSensor(data, "receiptNumber", consumer_no))
    entities.append(TNEBBillSensor(data, "paymentDate", consumer_no))
    add_entities(entities)

class TNEBBillData(object):
    """Representation of a TNEB Bill."""

    def __init__(self, consumer_no, username, password):
        """Initialize the portal."""
        self.consumerno = consumer_no
        self.username = username
        self.password = "".join(str(ord(c)+74).zfill(4) for c in password)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the portal."""
        headers={"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Content-Type": "application/x-www-form-urlencoded","Connection": "keep-alive"}
        headers["Referer"]=BASE_URL + "/awp/login";
        login_data = "j_username=" + self.username + "&j_password=" + self.password + "&submit=Login&j_idt78_input="

        try:
            s = requests.Session();
            response = s.post(BASE_URL + "/awp/logincheck", data=login_data, headers=headers, timeout=10)
            response = s.get(BASE_URL + "/awp/billStatus", headers=headers)

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'role': 'grid'})
            tr = table.findAll('tr', {'role': 'row'})
            counter = -1
            for i in tr:
                td = i.findAll('td', {'role': 'gridcell'})
                for j in td:
                    if j.text == self.consumerno:
                        form_data = "form%3Aj_idt106%3A" + str(counter) + "%3Aj_idt123"
                        break
                counter += 1

            data='javax.faces.partial.ajax=true&javax.faces.source=' + form_data + '&javax.faces.partial.execute=%40all&' + form_data + '=' + form_data + '&form=form&javax.faces.ViewState=e2s1'

            headers={"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Content-Type": "application/x-www-form-urlencoded", "Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive"}
            headers["Referer"]=BASE_URL + "/awp/billStatus?execution=e2s1";
            response = s.post(BASE_URL + "/awp/billStatus?execution=e2s1", data=data, headers=headers)

            obj = untangle.parse(response.text)

            headers={"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Content-Type": "application/x-www-form-urlencoded","Connection": "keep-alive"}
            headers["Referer"]=BASE_URL + "/awp/billStatus?execution=e2s1";
            response = s.get(BASE_URL + obj.partial_response.redirect['url'], headers=headers)

            d={}
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'billgrid'})
            d['consumerName'] = table.find('td', text='Name').findNext('td').text
            d['consumerNo'] = table.find('td', text='Consumer No').findNext('td').text
            d['phase'] = table.find('td', text='Phase').findNext('td').text
            d['meterNumber'] = table.find('td', text='Meter Number').findNext('td').text
            tbody = soup.find('tbody', {'id': 'j_idt98:j_idt308_data'})
            div = tbody.findAll('div', {'class': 'ui-dt-c'})
            d['readingDate'] = div[0].text
            d['meterReading'] = div[1].text
            d['usedUnits'] = div[2].text
            d['ccCharges'] = div[3].text
            d['otherCharges'] = div[4].text
            d['billAmount'] = div[5].text
            d['totalAmount'] = div[8].text
            d['dueDate'] = div[9].text
            d['billPaidAmount'] = div[10].text
            d['receiptNumber'] = div[11].text
            d['paymentDate'] = div[12].text

            self.data = json.loads(json.dumps(d));
            print(self.data)
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
        except KeyboardInterrupt:
            print("Someone closed the program") 

class TNEBBillSensor(Entity):
    """Representation of a TNEBBill sensor."""

    def __init__(self, data, sensor_type, consumer_no):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + consumer_no + '_' +  sensor_type
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()
        billdetails = self.data.data
        if (billdetails):
            if self.type == 'consumerName':
                self._state = billdetails['consumerName']
            elif self.type == 'consumerNo':
                self._state = billdetails['consumerNo']
            elif self.type == 'phase':
                self._state = billdetails['phase']
            elif self.type == 'meterNumber':
                self._state = billdetails['meterNumber']    
            elif self.type == 'readingDate':
                self._state = billdetails['readingDate']
            elif self.type == 'usedUnits':
                self._state = billdetails['usedUnits']    
            elif self.type == 'meterReading':
                self._state = billdetails['meterReading']    
            elif self.type == 'ccCharges':
                self._state = billdetails['ccCharges']    
            elif self.type == 'otherCharges':
                self._state = billdetails['otherCharges']    
            elif self.type == 'billAmount':
                self._state = billdetails['billAmount']    
            elif self.type == 'totalAmount':
                self._state = billdetails['totalAmount']    
            elif self.type == 'dueDate':
                self._state = billdetails['dueDate']    
            elif self.type == 'billPaidAmount':
                self._state = billdetails['billPaidAmount']    
            elif self.type == 'receiptNumber':
                self._state = billdetails['receiptNumber']    
            elif self.type == 'paymentDate':
                self._state = billdetails['paymentDate']    
