<?xml version='1.0' encoding='UTF-8'?>
<esdl:EnergySystem xmlns:esdl="http://www.tno.nl/esdl" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" description="Left" version="1.0" name="Left" id="90fe33ee-c6cf-472d-b7af-943ab745716d">
  <instance xsi:type="esdl:Instance" name="Instance1" id="9f411ea8-ca2d-4984-8fb3-8cac0a209168">
    <area xsi:type="esdl:Area" name="Area1" id="3f5444bd-f33b-487e-a2a9-344dd3aa85e4">
      <asset xsi:type="esdl:PVPark" name="PVPark_1680" id="16801ded-f4f9-4bfb-bad3-995d5a6f087f">
        <geometry xsi:type="esdl:Point" lat="52.49950372242746" lon="5.5096435546875" CRS="WGS84"/>
        <port xsi:type="esdl:OutPort" id="38b82cd9-21b5-4754-ac38-47270ec1ae5c" name="Out"/>
      </asset>
      <asset xsi:type="esdl:PVPark" name="PVPark_47b1" id="47b1d40a-644e-49d3-8556-e03272ec9f91">
        <geometry xsi:type="esdl:Point" lat="52.80608223985886" lon="6.053466796875001" CRS="WGS84"/>
        <port xsi:type="esdl:OutPort" id="db1b3d37-0844-4c6f-a4ca-6b6b4e84e963" name="Out"/>
      </asset>
      <asset xsi:type="esdl:PowerPlant" name="PowerPlant_ec1f" id="ec1f3382-3c52-4e9d-ad17-6835cba51f7e">
        <geometry xsi:type="esdl:Point" lat="52.52958999943304" lon="4.740600585937501" CRS="WGS84"/>
        <port xsi:type="esdl:InPort" id="10fc1160-8c92-4466-929f-97df62f81ab7" name="In"/>
        <port xsi:type="esdl:OutPort" id="c76387ef-3ac0-41b6-90bf-f291afe4ba2c" name="Out"/>
      </asset>
    </area>
  </instance>
</esdl:EnergySystem>
