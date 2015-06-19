angular.module('JaciApp.Preferences', ['JaciApp.Common']).controller('PreferencesController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    $scope.savePreferences = function(data){
        $http.post('/api/preferences', data).
            success(function(data, status, headers, config) {
                console.log("/api/preferences", data)
            }).
            error(function(data, status, headers, config) {
                console.log("/api/preferences", data)
                $rootScope.go("/");
            });
    };
});
