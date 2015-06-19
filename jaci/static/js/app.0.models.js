function Builder(data){
    // 'ready',      # no builds scheduled
    // 'scheduled',  # scheduled but not yet running
    // 'running',    # running
    // 'succeeded',  # finished with success, subprocess returned status 0
    // 'failed',     # finished with an error, subprocess returned status != 0
    var self = this;
    self.data = data;
    for (var key in data) {
        self[key] = data[key];
    }

    self.url = "#builders/" + self.id;

}
Builder.prototype.triggerBuild = function(branch){
    var self = this;
};

Builder.fromList = function(listOfBuilderData) {
    var results = {};
    for (var x in listOfBuilderData) {
        var item = listOfBuilderData[x];
        results[item.id] = item;
    }
    return results;
};
