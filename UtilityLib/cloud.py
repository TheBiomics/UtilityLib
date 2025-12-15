from .project import ProjectManager

class CloudManager(ProjectManager):
  ...


class AWSManager(CloudManager):
  ...


class GCPManager(CloudManager):
  ...