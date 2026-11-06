<?xml version='1.0' encoding='UTF-8'?>
<esdl:EnergySystem xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:esdl="http://www.tno.nl/esdl" version="2" id="5ef9819d-8366-4a3d-bcef-595038e1429c" description="" esdlVersion="v2401" name="SimpleES">
  <instance xsi:type="esdl:Instance" id="1d330384-a082-4ff5-a133-b95481ba63cf" name="Instance0">
    <area xsi:type="esdl:Area" id="3e0bed4f-a160-47d8-8b3b-33f36d021554" name="MainArea">
      <asset xsi:type="esdl:GenericProducer" name="GenericProducer1" id="19de7998-1da2-4f1e-815b-1d271bf0d9d4">
        <geometry xsi:type="esdl:Point" lat="52.143602398455315" lon="4.718627929687501" CRS="WGS84"/>
        <port xsi:type="esdl:OutPort" id="8a8951aa-246d-4e43-b85d-a6683f6d0c7b" connectedTo="d32ff396-6385-4295-9321-4d92d2f1edc2" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="Out"/>
        <port xsi:type="esdl:InPort" name="In" id="7501831e-af4e-415f-b746-d1a6cd13fb40"/>
      </asset>
      <asset xsi:type="esdl:GenericConsumer" name="GenericConsumer1" id="670b296a-aa7d-429c-a420-42d6a1c48ee4">
        <geometry xsi:type="esdl:Point" lat="52.15371445951162" lon="5.789794921875001" CRS="WGS84"/>
        <port xsi:type="esdl:InPort" connectedTo="7c4b5322-969e-4327-a7c5-9361a3d3bcd4" id="d137c680-eaab-4e5f-94ac-f581730061c3" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" name="Out" id="e8478c5a-81e8-4966-a1a3-2e3eb85d6de5"/>
      </asset>
      <asset xsi:type="esdl:HeatStorage" name="HeatStorage1" id="a6b7733d-3926-4359-a4e8-74f6d13751cf">
        <geometry xsi:type="esdl:Point" lat="52.26815737376817" lon="5.289916992187501" CRS="WGS84"/>
        <port xsi:type="esdl:InPort" connectedTo="c37d0992-2789-42e7-84c3-5b39d4fe4fe3" id="33d01a7b-cb5a-429c-a41c-dd89de451add" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" name="Out" id="e20c6573-df22-4505-a8be-3e30e9dd2105"/>
      </asset>
      <asset xsi:type="esdl:Pipe" length="38572.16" name="Pipe1" id="73b87475-4212-4073-a8c1-25e62c996f94">
        <geometry xsi:type="esdl:Line">
          <point xsi:type="esdl:Point" lat="52.143602398455315" lon="4.718627929687501"/>
          <point xsi:type="esdl:Point" lat="52.16382422414709" lon="5.283050537109375"/>
        </geometry>
        <port xsi:type="esdl:InPort" connectedTo="8a8951aa-246d-4e43-b85d-a6683f6d0c7b" id="d32ff396-6385-4295-9321-4d92d2f1edc2" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" id="da61b000-0e90-4691-b451-9ec728bfd8bd" connectedTo="1206c46d-1c9b-4556-b4db-7dc0566e2382" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="Out"/>
      </asset>
      <asset xsi:type="esdl:Pipe" length="34586.0" name="Pipe2" id="b7186826-3464-4f46-bb82-4199c7adc4a0">
        <geometry xsi:type="esdl:Line">
          <point xsi:type="esdl:Point" lat="52.16382422414709" lon="5.283050537109375"/>
          <point xsi:type="esdl:Point" lat="52.16382422414709" lon="5.284423828125"/>
          <point xsi:type="esdl:Point" lat="52.15371445951162" lon="5.789794921875001"/>
        </geometry>
        <port xsi:type="esdl:InPort" connectedTo="475d6ad2-0dbe-457a-bcc0-91a7feaf3dcf" id="6b1a2876-a66b-4d78-834f-6bb11d0154f0" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" id="7c4b5322-969e-4327-a7c5-9361a3d3bcd4" connectedTo="d137c680-eaab-4e5f-94ac-f581730061c3" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="Out"/>
      </asset>
      <asset xsi:type="esdl:Joint" name="Joint1" id="1332dd19-741d-46fa-8eab-2edc36dd5d59">
        <geometry xsi:type="esdl:Point" lat="52.16382422414709" lon="5.283050537109375"/>
        <port xsi:type="esdl:InPort" connectedTo="da61b000-0e90-4691-b451-9ec728bfd8bd" id="1206c46d-1c9b-4556-b4db-7dc0566e2382" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" id="475d6ad2-0dbe-457a-bcc0-91a7feaf3dcf" connectedTo="6b1a2876-a66b-4d78-834f-6bb11d0154f0 cf13d0ea-f4df-4a10-9dcf-3b2ff2739da7" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="Out"/>
      </asset>
      <asset xsi:type="esdl:Pipe" name="PipeS" length="11655.5" id="1f8177ee-7727-45f1-bbbb-6c3fa7d4a736">
        <geometry xsi:type="esdl:Line" CRS="WGS84">
          <point xsi:type="esdl:Point" lat="52.16382422414709" lon="5.283050537109375"/>
          <point xsi:type="esdl:Point" lat="52.2008737173322" lon="5.292663574218751"/>
          <point xsi:type="esdl:Point" lat="52.26815737376817" lon="5.289916992187501"/>
        </geometry>
        <port xsi:type="esdl:InPort" connectedTo="475d6ad2-0dbe-457a-bcc0-91a7feaf3dcf" id="cf13d0ea-f4df-4a10-9dcf-3b2ff2739da7" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="In"/>
        <port xsi:type="esdl:OutPort" id="c37d0992-2789-42e7-84c3-5b39d4fe4fe3" connectedTo="33d01a7b-cb5a-429c-a41c-dd89de451add" carrier="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b" name="Out"/>
      </asset>
    </area>
  </instance>
  <energySystemInformation xsi:type="esdl:EnergySystemInformation" id="f0a427de-4dfa-4c6b-947d-d705a8fb25e6">
    <carriers xsi:type="esdl:Carriers" id="348b1893-1990-4f5b-9dd0-8a4ca80b5a06">
      <carrier xsi:type="esdl:ElectricityCommodity" name="Electricity" id="34d4e1a7-0670-4730-aa6b-e14fd3ef2f4b"/>
    </carriers>
  </energySystemInformation>
</esdl:EnergySystem>
