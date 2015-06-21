angular.module('JaciApp.NewBuilder', ['JaciApp.Common']).controller('NewBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    // 'name': 'Device Management [unit tests]',
    // 'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
    // 'build_instructions': 'make test',

    $scope.builder = {
        'shell_script':[
            '#!/bin/bash',
            'set -e',
            'pip install virtualenv',
            'virtualenv .venv',
            'source .venv/bin/activate',
            'pip install -r requirements.txt || echo "skipped development.txt"',
            'pip install -r development.txt || echo "skipped development.txt"',
            'make'
        ].join('\n')
    };

    $scope.createBuilder = function(builder) {
        $http.post('/api/builder', builder).
            success(function(data, status, headers, config) {
                console.log("/api/builder OK");
                $rootScope.go('/');
            }).error($rootScope.defaultErrorHandler);
    };
});
