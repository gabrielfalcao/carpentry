angular.module('JaciApp.Preferences', ['JaciApp.Common']).controller('PreferencesController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    $rootScope.resetPollers();

    $scope.savePreferences = function(data){
        $http.post('/api/preferences', data).
            success(function(data, status, headers, config) {
                console.log("/api/preferences", data)
            }).
            error(function(data, status){
                notify('failed to retrieve preferences');
                console.log('failed to retrieve preferences', data, status);
            });
    };
});
