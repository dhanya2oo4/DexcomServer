from pydexcom import Dexcom
from dotenv import load_dotenv
import os
load_dotenv()
dexcom = Dexcom(username=os.getenv("USERNAME"), password = os.getenv("PASSWORD"), region="jp")
reading = dexcom.get_current_glucose_reading()
print(reading.mmol)