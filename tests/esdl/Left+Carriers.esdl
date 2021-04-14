<?xml version='1.0' encoding='UTF-8'?>
<esdl:EnergySystem xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:esdl="http://www.tno.nl/esdl" name="Left" version="1.0" description="Left" id="90fe33ee-c6cf-472d-b7af-943ab745716d">
  <instance xsi:type="esdl:Instance" id="9f411ea8-ca2d-4984-8fb3-8cac0a209168" name="Instance1">
    <area xsi:type="esdl:Area" id="3f5444bd-f33b-487e-a2a9-344dd3aa85e4" name="Area1">
      <asset xsi:type="esdl:PVPark" id="16801ded-f4f9-4bfb-bad3-995d5a6f087f" name="PVPark_1680">
        <port xsi:type="esdl:OutPort" name="Out" id="38b82cd9-21b5-4754-ac38-47270ec1ae5c"/>
        <geometry xsi:type="esdl:Point" CRS="WGS84" lat="52.49950372242746" lon="5.5096435546875"/>
      </asset>
      <asset xsi:type="esdl:PVPark" id="47b1d40a-644e-49d3-8556-e03272ec9f91" name="PVPark_47b1">
        <port xsi:type="esdl:OutPort" name="Out" id="db1b3d37-0844-4c6f-a4ca-6b6b4e84e963"/>
        <geometry xsi:type="esdl:Point" CRS="WGS84" lat="52.80608223985886" lon="6.053466796875001"/>
      </asset>
      <asset xsi:type="esdl:PowerPlant" id="ec1f3382-3c52-4e9d-ad17-6835cba51f7e" name="PowerPlant_ec1f">
        <port xsi:type="esdl:InPort" name="In" id="10fc1160-8c92-4466-929f-97df62f81ab7"/>
        <port xsi:type="esdl:OutPort" name="Out" id="c76387ef-3ac0-41b6-90bf-f291afe4ba2c"/>
        <geometry xsi:type="esdl:Point" CRS="WGS84" lat="52.52958999943304" lon="4.740600585937501"/>
      </asset>
    </area>
  </instance>
  <energySystemInformation xsi:type="esdl:EnergySystemInformation">
    <carriers xsi:type="esdl:Carriers">
      <carrier xsi:type="esdl:EnergyCarrier" name="Crude oil" energyContent="42.7" id="b2d2c781-fd13-483b-841a-72d1174aea35" emission="73.3">
        <energyContentUnit xsi:type="esdl:QuantityAndUnitType" perUnit="GRAM" multiplier="MEGA" unit="JOULE" physicalQuantity="ENERGY" perMultiplier="KILO"/>
        <emissionUnit xsi:type="esdl:QuantityAndUnitType" perUnit="JOULE" multiplier="KILO" unit="GRAM" physicalQuantity="EMISSION" perMultiplier="GIGA"/>
      </carrier>
    </carriers>
  </energySystemInformation>
</esdl:EnergySystem>
