import numpy as np
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock


class Dataset(object):
    """
    Parent class for datasets.
    Serves as a wrapper for LabRAD datasets.
    """

    def __init__(self, data_vault, context, dataset_location, reactor):
        super(Dataset, self).__init__()
        self.accessingData = DeferredLock()
        self.reactor = reactor
        self.context = context
        # dataset storage variables
        self.dataset_location = dataset_location
        self.data_vault = data_vault
        self.data = None
        self.points_per_grab = 1000
        self.last_index = 0
        self.updateCounter = 0
        # startup sequence
        self.connectDataVault()
        self.openDataset()
        self.setupListeners()


    # SET UP CONNECTION
    @inlineCallbacks
    def connectDataVault(self):
        yield self.accessingData.acquire()
        yield self.data_vault.cd(self.dataset_location[0], context=self.context)
        _, self.dataset_name = yield self.data_vault.open(self.dataset_location[1], context=self.context)
    
    @inlineCallbacks
    def openDataset(self):
        # open the dataset
        yield self.data_vault.cd(self.dataset_location[0], context=self.context)
        yield self.data_vault.open(self.dataset_location[1], context=self.context)
        # allocate array size based on dataset size
        dataset_shape = 0
        # support older data vault versions that don't have shape function
        try:
            dataset_shape = yield self.data_vault.shape(context=self.context)
        except Exception as e:
            _, all_dep = yield self.data_vault.variables(context=self.context)
            dataset_shape = (0, 1 + len(all_dep))
        self.data = np.zeros(dataset_shape)
        self.accessingData.release()

    @inlineCallbacks
    def setupListeners(self):
        yield self.data_vault.signal__data_available(11111, context=self.context)
        yield self.data_vault.addListener(listener=self.updateData, source=None, ID=11111, context=self.context)

    @inlineCallbacks
    def disconnectDataSignal(self):
        yield self.data_vault.removeListener(listener=self.updateData, source=None, ID=11111, context=self.context)


    # GETTERS
    @inlineCallbacks
    def getParameters(self):
        parameters = yield self.data_vault.parameters(context=self.context)
        parameterValues = []
        for parameter in parameters:
            parameterValue = yield self.data_vault.get_parameter(parameter, context=self.context)
            parameterValues.append((parameter, parameterValue))
        returnValue(parameterValues)

    @inlineCallbacks
    def getLabels(self):
        """
        Returns all trace names in the dataset.
        Returns:
            [str]:  a list containing the trace names.
        """
        yield self.accessingData.acquire()
        labels = []
        _, all_dep = yield self.data_vault.variables(context=self.context)
        # check for duplicate trace names
        for i in range(len(all_dep)):
            label_tmp = all_dep[i][0] + ' - ' + self.dataset_name
            # add the index in parentheses to the end
            # of the name to break the degeneracy
            if label_tmp in labels:
                label_tmp += ' (' + str(i) + ')'
            labels.append(label_tmp)
        self.accessingData.release()
        returnValue(labels)

    def updateData(self, c, msg):
        self.updateCounter += 1
        self.getData()

    @inlineCallbacks
    def getData(self):
        """
        Gets data in bunches at a time and adds them to self.data, which holds the dataset.
        """
        # acquire communication
        yield self.accessingData.acquire()
        # get data from the datavault
        data_tmp = yield self.data_vault.get(self.points_per_grab, context=self.context)
        data_tmp = np.array(data_tmp)
        next_index = self.last_index + np.shape(data_tmp)[0]
        # add to array if we have the space
        if next_index <= np.shape(self.data)[0]:
            self.data[self.last_index: next_index] = data_tmp
        # otherwise append to array
        else:
            self.data = np.append(self.data, data_tmp, axis=0)
        self.last_index = next_index
        # release communication
        self.accessingData.release()
