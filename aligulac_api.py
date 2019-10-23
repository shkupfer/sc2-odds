import requests
from os.path import join
from itertools import combinations

ROOT_URL = 'http://aligulac.com/api/v1/'


class AligulacAPI:
    def __init__(self, api_key, root_url=ROOT_URL):
        self.api_key = api_key
        self.root_url = root_url
        self.default_params = {'apikey': self.api_key}

    def get(self, addnl_url='', addnl_params=None):
        url = join(self.root_url, addnl_url)
        params = self.default_params.copy()
        if addnl_params:
            params.update(addnl_params)
        resp = requests.get(url, params=params)
        return resp

    def resources(self):
        resp = self.get()
        return resp.json()

    def schema(self, endpoint):
        path = '%s/schema/' % endpoint
        resp = self.get(path)
        return resp.json()

    def player(self, filters):
        addnl_params = filters.items()
        resp = self.get('player/', addnl_params)
        return resp.json()

    def player_name_from_id(self, p_id):
        id_fltr = {'id__exact': p_id}
        plyr_resp = self.player(id_fltr)
        return plyr_resp['objects'][0]['tag']

    def predictmatch(self, ida, idb, bo=1):
        url = 'predictmatch/%s,%s/' % (ida, idb)
        addnl_params = {'bo': bo}
        resp = self.get(url, addnl_params)
        return resp.json()

    def best_player_id_by_name(self, name):
        addnl_params = {'tag__exact': name, 'order_by': '-current_rating__rating'}
        resp = self.get('player/', addnl_params)
        jsn = resp.json()
        plyr_id = jsn['objects'][0]['id']
        return plyr_id


class Player:
    def __init__(self, alig_api, p_name=None, p_id=None):
        self.alig_api = alig_api
        self.p_name = p_name
        self.p_id = p_id

    def get_name_id(self):
        if not self.p_name and not self.p_id:
            raise Exception("Need either player name or player ID")
        elif self.p_name and not self.p_id:
            self.p_name = self.p_name
            self.p_id = self.alig_api.best_player_id_by_name(self.p_name)
        elif self.p_id and not self.p_name:
            self.p_id = self.p_id
            self.p_name = self.alig_api.player_name_from_id(self.p_id)

    def __str__(self):
        return "%s (ID: %s)" % (self.p_name, self.p_id)


class Match:
    def __init__(self, alig_api, pla, plb, bo=1):
        self.alig_api = alig_api
        self.bo = bo

        if type(pla) is str:
            self.pla = Player(alig_api, p_name=pla)
        elif type(pla) is int:
            self.pla = Player(alig_api, p_id=pla)
        elif type(pla) is Player:
            self.pla = pla
        else:
            raise Exception("Players should be Players, strings, or integers")
        self.pla.get_name_id()

        if type(plb) is str:
            self.plb = Player(alig_api, p_name=plb)
        elif type(plb) is int:
            self.plb = Player(alig_api, p_id=plb)
        elif type(plb) is Player:
            self.plb = plb
        else:
            raise Exception("Players should be strings or integers")
        self.plb.get_name_id()

        self.predicted = False
        self.pred_json = None
        self.proba = None
        self.probb = None
        self.probs_dct = None

    def predict(self):
        if self.predicted:
            print("Match has already been predicted")
        else:
            self.pred_json = self.alig_api.predictmatch(self.pla.p_id, self.plb.p_id, bo=self.bo)
            self.proba = self.pred_json['proba']
            self.probb = self.pred_json['probb']

            self.probs_dct = {self.pla: self.proba,
                              self.plb: self.probb}

            self.predicted = True

    def __str__(self):
        if self.predicted:
            return "Best of {0} match between {1} (win probability: {2}) and {3} (win probability: {4})".format(self.bo, self.pla, self.proba, self.plb, self.probb)
        else:
            return "Best of {0} match between {1} and {2} (not yet predicted)".format(self.bo, self.pla, self.plb)


class DualGroup:
    def __init__(self, alig_api, plyrs, bo=1):
        self.alig_api = alig_api
        self.bo = bo

        if len(plyrs) != 4:
            raise Exception("Need exactly 4 players for a dual tournament group")

        if not all([type(plyr) is Player for plyr in plyrs]):
            raise Exception("All players should be instances of Player")
        else:
            self.plyrs = plyrs

        self.predicted = False
        self.pred_json = None
        self.probs_dct = None

        self.pos_matches = {frozenset((pla, plb)): Match(alig_api, pla, plb, bo=bo) for pla, plb in combinations(self.plyrs, 2)}

    def get_names_ids(self):
        for plyr in self.plyrs:
            plyr.get_name_id()

    def predict(self):
        # TODO: Finish this
        pass

    def __str__(self):
        return "Dual Tournament group (best of %s matches) with players: %s" % (self.bo, ', '.join([str(plyr) for plyr in self.plyrs]))
