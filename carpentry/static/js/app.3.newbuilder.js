angular.module('CarpentryApp.NewBuilder', ['CarpentryApp.Common']).controller('NewBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    // 'name': 'Device Management [unit tests]',
    // 'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
    // 'build_instructions': 'make test',
    $rootScope.resetPollers();
    $scope.saveInProcess = false;

    $scope.builder = {
        'generate_ssh_keys': true,
        'name': $rootScope.user.name + "'s Project",
        'git_uri': 'git@github.com:'+$rootScope.user.login+'/yourrepo.git',
        'shell_script':[
            "#!/bin/bash",
            '',
            "for x in `seq 100`; do",
            "    date;",
            "    sleep 0.1;",
            "done"
        ].join('\n')
    };

    $scope.createBuilder = function(builder) {
        $scope.saveInProcess = true;

        $http.post('/api/builder', builder).
            success(function(data, status, headers, config) {
                $scope.saveInProcess = false;

                console.log("/api/builder OK");
                $rootScope.go('/');
            }).error(function(data, status){
                $scope.saveInProcess = false;
                if (status !== 502) {
                    notify('Failed to create builder');
                }
                console.log('Failed to create builder', status, data);
            });
    };
});
