import json


class Dashboard:
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def load(self):
        if self.data is None:
            try:
                with open(self.filename, 'r') as fd:
                    self.data = json.load(fd)
            except Exception as e:
                print(f'*** Unable to parse {self.filename}, error: {e} ***')
                return False
        return True

    def save(self, filename=None, indent=2):
        if filename is None:
            filename = self.filename
        with open(filename, 'w') as fd:
            json.dump(self.data, fd, indent=indent)

    def update_datasources(self, datasources):
        if not self.load():
            return None

        templating = self.data.get('templating', None)
        if templating is None:
            print(f'*** Unable to find templating in {self.filename} ***')
            templating = {'list': []}
            self.data['templating'] = templating

        templating_list = templating.get('list', None)
        if templating_list is None:
            print(f'*** Unable to find templating list in {self.filename} ***')
            templating_list = []
            self.data['templating']['list'] = templating_list

        template_datasource = next((it for it in templating_list if it.get('name', '') == 'datasource'), None)
        if template_datasource is None:
            print(f'*** Unable to find templating datasource in {self.filename} ***')
            templating_list += self._default_datasource
        elif template_datasource.get('type', '') == 'custom':
            template_datasource['current']['text'] = datasources
            template_datasource['current']['value'] = datasources

        for it in templating_list:
            if it.get('type', '') == 'query':
                if template_datasource is not None:
                    it['datasource'] = '$datasource'
                if it.get('name', '') in ('hostname', 'nodes', 'wlm', 'category', 'job_id'):
                    it['regex'] = '/.*"(.*)".*/'

        panels = self.data.get('panels', None)
        if panels is None:
            print(f'*** Unable to find templating in {self.filename} ***')
        else:
            for it in panels:
                it['datasource'] = '$datasource'

        version = self.data.get('version', 0) + 1
        self.data['version'] = version
        return version

    @property
    def _default_datasource(self):
        return {"current": {"selected": True,
                            "tags": [],
                            "text": [],
                            "value": []},
                "error": None,
                "hide": 0,
                "includeAll": False,
                "label": None,
                "multi": False,
                "name": "datasource",
                "options": [],
                "query": "prometheus",
                "queryValue": "",
                "refresh": 1,
                "regex": "",
                "skipUrlSync": False,
                "type": "datasource"}
