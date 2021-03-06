angular.module('CarpentryApp.Build', [
    'CarpentryApp.Common',
    'ui.bootstrap.progressbar'
]).controller('BuildController', function ($rootScope, $scope, $state, $http, $sce, notify, $stateParams) {
    
    $scope.html_output = $sce.trustAsHtml('loading...');

    $scope.build_id = $stateParams.build_id;
    $scope.eof = false;

    $scope.calculateDockerProgress = function(build){
        var progressDetail = build.docker_status.progressDetail;
        var result = progressDetail.total * (progressDetail.current / 100);
        console.log("docker progress: " + result + "%");
        return result;
    };

    $scope.html_output = null;
    function get_build() {
        if (!$stateParams.build_id) {
            console.log("Invalid build id:", $stateParams);
            return;
        }
        var url = '/api/build/'+$stateParams.build_id;
        $http.get(url).success(function (data, status, headers, config) {
            $scope.build = data;
            $scope.html_output = $sce.trustAsHtml(data.stdout);
            console.log(data);
        }).error(function (data, status, headers, config) {
            if (!status) {
                console.log("server did not respond to" + url);
                return;
            }
            if (status !== 502) {
                notify('failed to retrieve build: '+ status);
            }
            console.log('failed ' + url, status);
            clearInterval(poller);
            $scope.html_output = null;
            $rootScope.go("/");
            var progressDetail = build.docker_status.progressDetail;
            var result = progressDetail.total * (progressDetail.current / 100);
            $scope.value = result;
        });

    }
    var limit = 720;
    var counter = 0;

    $rootScope.resetPollers();
    $rootScope.buildPoller = setInterval(function(){
        counter++;
        if (counter > 720) {
            clearInterval($rootScope.buildPoller);
        }
        get_build();
    }, 500);
    get_build();
    $scope.deleteBuild = function(build){
        $http
            .delete('/api/build/' + build.id)
            .success(function(data, status, headers, config) {
                notify("build deleted!");
            })

            .error(function(data, status, headers, config) {
                console.log('failed to delete build');
            });

    };
});
