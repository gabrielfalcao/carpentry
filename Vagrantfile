Vagrant.require_version ">= 1.5.1"

Vagrant.configure("2") do |config|
  config.ssh.forward_agent = true
  config.vm.define "jaci-vm" do |c|
    c.vm.box = "ubuntu/trusty64"
    c.vm.network :forwarded_port, guest: 9000, host: 9000
    c.vm.network :forwarded_port, guest: 5000, host: 5000

    c.vm.provider "virtualbox" do |v|
      # https://github.com/jpetazzo/pipework#virtualbox
      v.customize ['modifyvm', :id, '--nicpromisc1', 'allow-all']
      v.memory = 8192
    end

    c.vm.provision :ansible do |ansible|
      ansible.playbook = "playbook.yml"
      # ansible.verbose = 'vvvv'
      ansible.extra_vars = {
            ansible_ssh_user: 'vagrant',
            ansible_connection: 'ssh',
            ansible_ssh_args: '-o ForwardAgent=yes',
        }
    end
  end
end
