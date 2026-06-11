from dataclasses import dataclass
from typing import Optional

from pyecore.resources import Resource, URI

from esdl.resource_handler import ResourceHandlerBase
from esdlproject import ESDLProject as Project


@dataclass
class EnergyProjectData:
    """
    Relevant data for an energy project in the resource set.
    """

    energy_project: Project
    uri: URI
    resource: Resource


class EnergyProjectHandlerMixin(ResourceHandlerBase):
    """
    Mixin class designed to be mixed in to the EnergySystemHandler. The reason to make
    this a mixin is so that 1) support is optional, and 2) to compartmentalize the
    functionality, and 3) to define a model for future extensions.

    Contains functions for handling energy projects.
    """

    def get_energy_project_data(self) -> Optional[EnergyProjectData]:
        """
        Retrieve all relevant data for an energy project in the handler, if any.
        """
        for key in self.rset.resources.keys():
            resource = self.rset.resources[key]
            resource_contents = resource.contents[0]
            if isinstance(resource_contents, Project):
                return EnergyProjectData(resource_contents, key, resource)
        return None

    def get_energy_project(self) -> Optional[Project]:
        """
        Retrieve the energy project in the handler, if any.
        """
        energy_project_data = self.get_energy_project_data()
        if energy_project_data:
            return energy_project_data.energy_project
        return None

    def load_esdl_project(self):
        """
        Loads energy project and overwrites the currently active energy project.
        """
        energy_project_data = self.get_energy_project_data()
        if energy_project_data:
            self.rset.remove_resource(energy_project_data)
