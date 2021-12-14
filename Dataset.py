'''
Parent class for datasets.
'''

import numpy as np
from PyQt5.QtCore import QObject
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock


class Dataset(QObject):
    
    def __init__(self, data_vault, context, dataset_location, reactor):
        super(Dataset, self).__init__()
        self.data = None
        self.accessingData = DeferredLock()
        self.reactor = reactor
        self.dataset_location = dataset_location
        self.data_vault = data_vault
        self.updateCounter = 0
        self.context = context
        self.connectDataVault()
        self.setupListeners()

        # dataset storage variables
        self.points_per_grab = 1000
        self.last_index = 0

        # startup sequence
        self.connectDataVault()
        self.setupListeners()

    @inlineCallbacks
    def connectDataVault(self):
        yield self.data_vault.cd(self.dataset_location[0], context=self.context)
        path, dataset_name = yield self.data_vault.open(self.dataset_location[1], context=self.context)
        self.dataset_name = dataset_name

    @inlineCallbacks
    def setupListeners(self):
        yield self.data_vault.signal__data_available(11111, context=self.context)
        yield self.data_vault.addListener(listener=self.updateData, source=None, ID=11111, context=self.context)

    @inlineCallbacks
    def openDataset(self):
        yield self.data_vault.cd(self.dataset_location[0], context=self.context)
        yield self.data_vault.open(self.dataset_location[1], context=self.context)

    @inlineCallbacks
    def getParameters(self):
        parameters = yield self.data_vault.parameters(context=self.context)
        parameterValues = []
        for parameter in parameters:
            parameterValue = yield self.data_vault.get_parameter(parameter, context=self.context)
            parameterValues.append((parameter, parameterValue))
        returnValue(parameterValues)

    def updateData(self, x, y):
        self.updateCounter += 1
        self.getData()

    @inlineCallbacks
    def getData(self):
        """
        Gets data in bunches at a time and adds
        them to self.data which holds the dataset.
        """
        yield self.accessingData.acquire()
        # get data from the datavault
        Data = yield self.data_vault.get(self.points_per_grab, context=self.context)
        Data = np.array(Data)
        rows = np.shape(Data)[0]
        # acquire communication
        if self.data is not None:
            self.data[self.last_index: self.last_index + rows] = Data
            self.last_index += rows
        else:
            dataset_shape = yield self.data_vault.shape(context=self.context)
            self.data = np.zeros(dataset_shape)
            self.data[self.last_index: self.last_index + rows] = Data
            self.last_index += rows
        self.accessingData.release()

    @inlineCallbacks
    def getLabels(self):
        labels = []
        yield self.openDataset()
        _, all_dep = yield self.data_vault.variables(context=self.context)
        for i in range(len(all_dep)):
            label_tmp = all_dep[i][0] + ' - ' + self.dataset_name
            if label_tmp in labels:
                label_tmp += ' (' + str(i) + ')'
            labels.append(label_tmp)
        returnValue(labels)

    @inlineCallbacks
    def disconnectDataSignal(self):
        yield self.data_vault.removeListener(listener=self.updateData, source=None, ID=11111, context=self.context)
