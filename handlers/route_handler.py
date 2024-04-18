import math
import copy
import numpy
from sklearn.cluster import KMeans as km
import googlemaps as gmaps
import warnings

class GoogleMapsAPI:
    fields = ['dine_in', 'price_level', 'serves_beer', 'serves_breakfast', 'serves_dinner', 'serves_lunch',
              'serves_wine', 'serves_vegetarian_food',
              'wheelchair_accessible_entrance']  # attribute fields of establishment to be added

    fileNameTrain = 'BarAttributesTrain'
    fileNameTest = 'BarAttributesTest'
    fileType = '.txt'

    placeIDs = []  # initialise placeIDs list
    placeNames = []  # initialise placeNames list

    currCoords = ''
    api_key = ''  # Need to use an API key

    search = 'pub'

    def __init__(self, gm):
        self.gm = gm

    def getSingleAttribute(self, coord):

        # gm = gmaps.Client(key=self.api_key)

        offset = 1  # how much of potential location matches the searchTerm
        biasRadius = 0  # radius of closeness bias from long/lat of device
        lang = 'None'  # set default language - English
        minP = 0  # minimum price range for establishments
        maxP = 4  # maximum price range for establishments
        openNow = False  # has to be open now to be added
        placeType = 'bar'  # type of establishment
        page_token = 'ATplDJbP_zHMMJ9qiKRPlCVeqhtNFJx60ZO-msVYtwx7NmwpU_b7gqVNBwE7DnPASf8T9zDN8KV811GPBrsBzXkxa0Wqs-hTZyyqMo6jgZCiD2o7hQvYQ2n8DPCXU_0TvEKGvC0dZVKWYb7P-B5wXBWrjiy97j5QsZwkO7_QGDXiNf1Ftdl681nB4GpSd4IkYvnHlUWNCP4YYAm3iFSvK2rPj74XdCSX4Sl1ZhumpPpZFusmjSrRi2DkTLxX1Ye2gI1bkCeJ-ZEQXTfKiVuymKvIDL9-pq2kCwgCC-EpuTfZcqdTwedLS9cflxCIm_IDc2tiAIzHk_JpDuxTG-Y58sneT1ulaPjmhj-BL4m2_FioIMq-59ez5uojU67vMCoi_OckTp4iz0sZJuzt-Bn4PhQXY8KyYpOFhZPXD6Fa5_3bzRwU4W3Pjik7k51QlYyMN5Y2eVcqZNvm'
        searchTerm = ''
        sess_token = ''

        out = self.gm.places(searchTerm, coord, biasRadius, lang, minP, maxP, openNow, placeType,
                             page_token)  # find all establishments with parameters

        add = self.gm.place(((out['results'])[0])['place_id'], sess_token, self.fields, lang, False,
                            'most_relevant')  # get attributes from each establishment with given parameters

        return [add['result']]

    def getKeyAttributes(self, currCoords, searchTerm):

        # gm = gmaps.Client(key=self.api_key) # set up client with API key

        # searchTerm -> key term to search for places
        offset = 1  # how much of potential location matches the searchTerm
        startLocation = currCoords  # set longitude and latitude
        biasRadius = 100  # radius of closeness bias from long/lat of device
        lang = 'None'  # set default language - English
        minP = 0  # minimum price range for establishments
        maxP = 4  # maximum price range for establishments
        openNow = False  # has to be open now to be added
        placeType = 'bar'  # type of establishment
        page_token = 'ATplDJbP_zHMMJ9qiKRPlCVeqhtNFJx60ZO-msVYtwx7NmwpU_b7gqVNBwE7DnPASf8T9zDN8KV811GPBrsBzXkxa0Wqs-hTZyyqMo6jgZCiD2o7hQvYQ2n8DPCXU_0TvEKGvC0dZVKWYb7P-B5wXBWrjiy97j5QsZwkO7_QGDXiNf1Ftdl681nB4GpSd4IkYvnHlUWNCP4YYAm3iFSvK2rPj74XdCSX4Sl1ZhumpPpZFusmjSrRi2DkTLxX1Ye2gI1bkCeJ-ZEQXTfKiVuymKvIDL9-pq2kCwgCC-EpuTfZcqdTwedLS9cflxCIm_IDc2tiAIzHk_JpDuxTG-Y58sneT1ulaPjmhj-BL4m2_FioIMq-59ez5uojU67vMCoi_OckTp4iz0sZJuzt-Bn4PhQXY8KyYpOFhZPXD6Fa5_3bzRwU4W3Pjik7k51QlYyMN5Y2eVcqZNvm'  # previous search token

        out = self.gm.places(searchTerm, startLocation, biasRadius, lang, minP, maxP, openNow, placeType,
                             page_token)  # find all establishments with parameters

        for i in out['results']:  # loop to add datum to placeNames and placeIDs
            self.placeNames.append((i['name']))  # add to placeNames
            self.placeIDs.append(i['place_id'])  # add to placeIDs

        dataAttributes = []  # initialise dataAttributes
        sess_token = 'None'  # session token is set to none

        for i in self.placeIDs:  # loop to add attributes to dataAttributes list
            add = self.gm.place(i, sess_token, self.fields, lang, False,
                                'most_relevant')  # get attributes from each establishment with given parameters

            dataAttributes.append(add['result'])  # add attributes to dataAttributes

        return (dataAttributes)

    def getEstabs(self, coords):

        # gm = gmaps.Client(self.api_key) # set up client with API key

        placeNames = []
        placeIDs = []

        searchTerm = 'pubs'

        # searchTerm -> key term to search for places
        biasRadius = 100  # radius of closeness bias from long/lat of device
        lang = 'None'  # set default language - English
        minP = 0  # minimum price range for establishments
        maxP = 4  # maximum price range for establishments
        openNow = False  # has to be open now to be added
        placeType = 'bar'  # type of establishment
        page_token = 'ATplDJbP_zHMMJ9qiKRPlCVeqhtNFJx60ZO-msVYtwx7NmwpU_b7gqVNBwE7DnPASf8T9zDN8KV811GPBrsBzXkxa0Wqs-hTZyyqMo6jgZCiD2o7hQvYQ2n8DPCXU_0TvEKGvC0dZVKWYb7P-B5wXBWrjiy97j5QsZwkO7_QGDXiNf1Ftdl681nB4GpSd4IkYvnHlUWNCP4YYAm3iFSvK2rPj74XdCSX4Sl1ZhumpPpZFusmjSrRi2DkTLxX1Ye2gI1bkCeJ-ZEQXTfKiVuymKvIDL9-pq2kCwgCC-EpuTfZcqdTwedLS9cflxCIm_IDc2tiAIzHk_JpDuxTG-Y58sneT1ulaPjmhj-BL4m2_FioIMq-59ez5uojU67vMCoi_OckTp4iz0sZJuzt-Bn4PhQXY8KyYpOFhZPXD6Fa5_3bzRwU4W3Pjik7k51QlYyMN5Y2eVcqZNvm'  # previous search token

        out = self.gm.places(searchTerm, coords, biasRadius, lang, minP, maxP, openNow, placeType,
                             page_token)  # find all establishments with parameters

        crds = []

        for i in range(len(out['results'])):
            crds.append(((out['results'][i]['geometry']['location']['lat']),
                         (out['results'][i]['geometry']['location']['lng'])))

        for i in out['results']:  # loop to add datum to placeNames and placeIDs
            placeNames.append((i['name']))  # add to placeNames
            placeIDs.append(i['place_id'])  # add to placeIDs

        ou = []
        ou.append(placeNames)
        ou.append(placeIDs)
        ou.append(crds)

        return ou

    def get_coords(self, loc):

        try:
            geo = self.gm.geocode(loc)
            place = geo[0]['geometry']['location']
            lat = place['lat']
            lon = place['lng']

            return lon, lat
        except Exception as e:
            return False

    def correctFormat(self, data):
        # data is the list of dict for the establishment data

        keyList = []
        out = []
        line = ''

        for i in data:
            line = self.alter(i)
            out.append(line)
            line = ''
        return out

    def alter(self, data):
        # data should be dictionary of establishment data - single instance

        line = ''

        for i in self.fields:
            if self.contains(data.keys(),
                             i):  # if data contains the value in fields it will then check the value to return 0 or 1. If not in there it will default to 0
                if data[i] == True:
                    line += '1'
                else:
                    line += '0'
            else:
                line += '0'

        return line

    def contains(self, data, inp):
        # data should be list

        found = False
        for i in data:
            if i == inp:
                found = True
        return found

    def getData(self, data):
        # data should be a list of attributes 1 or 0 of all the same length

        count = len(data[0])
        attr = ''
        out = []

        for i in data:
            for j in range(count):
                attr += i[j] + ' '
            out.append(attr)
            attr = ''

        testLen = 5  # add function to calculate number of tests for
        trainData = out[testLen + 1:]
        testData = out[0:testLen]

    def produceSingleAttribute(self, coords):

        data = self.correctFormat(self.getSingleAttribute(coords))

        count = len(data[0])
        attr = ''
        produceAttr = []

        for i in data:
            for j in range(count):
                attr += i[j] + ' '
            produceAttr.append(attr)
            attr = ''

        return produceAttr

    def produceAttributes(self, coords):
        data = self.correctFormat(self.getKeyAttributes(coords, self.search))

        count = len(data[0])
        attr = ''
        produceAttr = []

        for i in data:
            for j in range(count):
                attr += i[j] + ' '
            produceAttr.append(attr)
            attr = ''

        return produceAttr

    def getDistanceTo(self, sp, ep):
        # Gets the distance between sp and ep
        # gmaps = gmaps.Client(key=self.api_key)
        result = self.gm.distance_matrix(sp, ep)
        distanceInM = result['rows'][0]['elements'][0]['distance']['text']
        return distanceInM

    def getTimeTo(self, sp, ep):
        # get the time it takes to go from sp to ep
        # gmaps = gmaps.Client(key=self.api_key)
        result = self.gm.distance_matrix(sp, ep)
        time_taken = result['rows'][0]['elements'][0]['duration']['text']
        return time_taken

    def getSearch(self):
        return self.search

    def getPlaceNames(self):
        return self.placeNames

    def getPlaceIDs(self):
        return self.placeIDs


class KMeans:
    model = ''

    def __init__(self, gm):
        self.gm = gm

    def getDataset(self, filename):
        data = ''
        try:
            f = open(filename, 'r')
            data = f.read()
        except:
            print('Error Reading File')

        content = data.splitlines()

        data = []

        for i in content:
            data.append(i.split())

        # Data is array of arrays with attributes

        numpyArrs = []

        for i in data:
            numpyArrs.append(numpy.array(i))

        return numpyArrs

    def formDataset(self, data):
        out = []
        numpyArrs = []

        for i in data:
            out.append(i.split())

        for i in out:
            numpyArrs.append(numpy.array(i))

        return numpyArrs

    def buildModel(self, data, n_clusters):

        model = km(n_init=n_clusters, n_clusters=n_clusters)
        self.model = model

        model.fit(data)

        all_pred = model.predict(data)

        return all_pred

    def predictClass(self, coords):

        datum = self.formDataset(self.gm.produceSingleAttribute(coords))

        prediction = self.model.predict(datum)

        return prediction

    def getModel(self):
        return self.model

    def sortClass(self, pred, data, names):
        rec = []
        for i in range(len(data)):
            if data[i] == pred:
                rec.append(names[i])
        return rec


class Route:
    noOfEstab = 0
    searchTerm = 'pub'
    finalRoute = []
    final_route_id = []
    final_route_coords = []
    prevResult = []

    warnings.filterwarnings('ignore')

    def __init__(self, gm, db):
        self.gm = gm
        self.db = db

    list_of_dict = []
    def createRoute(self, sp, classNo, no_of_estab):

        correctPlaces = []
        correct_coords = []
        correct_place_id = []
        kme = KMeans(self.gm)
        gme = GoogleMapsAPI(self.gm)
        estabs = kme.formDataset(gme.produceAttributes(sp))
        placeNames = gme.getPlaceNames()
        place_id = gme.getPlaceIDs()

        pred = kme.buildModel(estabs, classNo)

        iniPred = kme.predictClass(sp)

        for i in range(len(pred) - 1):
            if iniPred == pred[i]:

                for i in range(len(placeNames)):
                    self.list_of_dict.append({'correct_place': placeNames[i], 'place_id': correct_place_id[i], 'place_coords': correct_coords[i]})

                #correctPlaces.append(placeNames[i])
                #correct_place_id.append(place_id[i])
                #correct_coords.append(gme.get_coords(placeNames[i]))

        correctPlaces = self.removeDuplicates(correctPlaces)

        if len(correctPlaces) >= no_of_estab:
            self.finalRoute = correctPlaces[:no_of_estab]
            self.final_route_id = correct_place_id[:no_of_estab]
            self.final_route_coords = correct_coords[:no_of_estab]
            return True  # need to only return number of estab amount
        else:
            self.createRoute(sp, (classNo - 1), no_of_estab)

    def removeDuplicates(self, data):

        out = []

        for i in data:
            if not (i in out):
                out.append(i)
        return out

    def getFinalRoute(self):

        return self.list_of_dict

    def saveRoute(self, route, user_id):

        try:
            rte = []
            for i in route:
                rte.append(str(i) + ',')

            query = 'UPDATE SavedRoutes SET VALUES(COUNT(RouteID) + 1, %s, %s, %s, %s)'
            self.db.execute(query, 0, len(route), route, 0, user_id)
            self.db.commit()

            return True

        except Exception as e:
            print(e)
            return False
