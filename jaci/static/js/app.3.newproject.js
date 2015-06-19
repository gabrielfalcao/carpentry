angular.module('JaciApp.NewBuilder', ['JaciApp.Common']).controller('NewBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    // 'name': 'Device Management [unit tests]',
    // 'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
    // 'build_instructions': 'make test',


    $scope.createBuilder = function(builder) {
        $http.post('/api/builder', builder).
            success(function(data, status, headers, config) {
                console.log("/api/builder OK")
            }).
            error(function(data, status, headers, config) {
                console.log("/api/builder FAILED")
            });
    };
});
