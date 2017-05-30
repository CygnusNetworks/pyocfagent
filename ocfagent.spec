%global pyname ipcalc
%global version 0.10

Name:           python-%{pyname}
Version:        %{version}
Release:        1%{?dist}
Summary:        Python ipcalc module

License:        Python
Source0:        python-ocfagentc-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel

%description
Python OCF Resource Agent Framework for Corosync/Pacemaker http://clusterlabs.org
This is a Python OCF Cluster Resource Agent Framework for implementing OCF Resource Agents in Python.

%prep
%setup -q -n %{pyname}-%{version}


%build
%{__python2} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python2} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%files
%{python2_sitelib}/*


%changelog
