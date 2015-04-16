angular.module("JaciApp.Index", [
    "JaciApp.Common",
]).controller('IndexController', function($rootScope, $scope, $state, $http, $cookies, hotkeys, notify){
    hotkeys.add({
        combo: 'ctrl+D',
        description: 'Refresh the API cache',
        callback: function(){
            RefreshCache();
        }
    });
});
