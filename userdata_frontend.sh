# install maven
sudo wget https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
sudo sed -i s/\$releasever/6/g /etc/yum.repos.d/epel-apache-maven.repo
sudo yum install -y apache-maven
sudo yum install java-1.8.0-devel -y
sudo update-alternatives --set java /usr/lib/jvm/java-11-amazon-corretto.x86_64/bin/java

# run
git clone https://github.com/andy-ecloud/cloud-edge-lab-template.git ~/cloud-edge-lab-template
mvn install -f ~/cloud-edge-lab-template/api-parent/pom.xml
mvn install -f ~/cloud-edge-lab-template/api-frontend/pom.xml
mvn spring-boot:run -f ~/cloud-edge-lab-template/api-frontend/pom.xml