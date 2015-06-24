angular.module('JaciApp.NewBuilder', ['JaciApp.Common']).controller('NewBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    // 'name': 'Device Management [unit tests]',
    // 'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
    // 'build_instructions': 'make test',
    $rootScope.resetPollers();

    $scope.builder = {
        'generate_ssh_keys': true,
        'name': $rootScope.user.name + "'s Project",
        'git_uri': 'git@github.com:'+$rootScope.user.login+'/yourrepo.git',
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
            }).error(function(data, status){
                notify('Failed to create builder');
                console.log('Failed to create builder', status, data);
            });
    };
});
