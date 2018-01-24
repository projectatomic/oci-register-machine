%global with_devel 0
%global with_bundled 1

%if 0%{?fedora}
%global with_debug 1
%global with_check 1
%global with_unit_test 0
%else
%global with_debug 1
# no test files so far
%global with_check 0
# no test files so far
%global with_unit_test 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         projectatomic
%global repo            oci-register-machine
# https://github.com/projectatomic/oci-register-machine
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          cd1e331b78273c9b87d737f46f8d0917b72c546d
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           %{repo}
Version:        0
Release:        6.1.git%{shortcommit}%{?dist}
Summary:        Golang binary to register OCI containers with systemd-machined
License:        ASL 2.0
URL:            https://%{import_path}
Source0:        https://%{import_path}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%if ! 0%{?with_bundled}
BuildRequires: golang(gopkg.in/yaml.v1)
BuildRequires: golang(github.com/godbus/dbus)
%endif
BuildRequires:   go-md2man
%if 0%{?fedora}
Requires: systemd-container
%else
Requires: systemd
%endif

%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch
Provides:      golang(%{import_path}) = %{version}-%{release}

%if 0%{?with_check} && ! 0%{?with_bundled}
%endif

%description devel
%{summary}

This package contains the source files for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{name}-%{commit}

%build
mkdir -p src/github.com/projectatomic
ln -s ../../../ src/github.com/projectatomic/oci-register-machine

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
export GOPATH=$(pwd):$(pwd)/Godeps/_workspace:%{gopath}
%endif

make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

# source code for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . -iname "*.go" \! -iname "*_test.go") ; do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}%{gopath}:%{gopath}
%else
export GOPATH=%{buildroot}%{gopath}:$(pwd)/Godeps/_workspace:%{gopath}
%endif

%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%config(noreplace) %{_sysconfdir}/%{name}.conf
%doc %{name}.1.md README.md
%dir %{_libexecdir}/oci
%dir %{_libexecdir}/oci/hooks.d
%{_libexecdir}/oci/hooks.d/%{name}
%{_mandir}/man1/%{name}.1*
%dir %{_usr}/share/containers/oci/hooks.d
%{_usr}/share/containers/oci/hooks.d/oci-register-machine.json

%if 0%{?with_devel}
%files devel -f devel.file-list
%license LICENSE
%doc %{name}.1.md README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license LICENSE
%doc %{name}.1.md README.md
%endif

%changelog
* Wed Jan 24 2018 Daniel Walsh <dwalsh@redhat.com> - 0-6.1.git
- Support stage being passed in via environment variable

* Thu Jan 4 2018 Daniel Walsh <dwalsh@redhat.com> - 0-5.13.git
- Disable this hook by default.
- Not many people are using it, and it is causing some issues with Docker.

* Thu Dec 21 2017 Daniel Walsh <dwalsh@redhat.com> - 0-5.12.git
- Fix using json file to describe stages to run hook in.

* Wed Sep 13 2017 Daniel Walsh <dwalsh@redhat.com> - 0-5.11.gitcbf1b8f
- Add support for CRI-O
- Fix for newer versions of runc

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-5.10.gitcbf1b8f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-4.10.gitcbf1b8f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 14 2017 Daniel Walsh <dwalsh@redhat.com> - 0-3.9.git76fc0b3
- Add missing bindings

* Wed Jun 28 2017 Daniel Walsh <dwalsh@redhat.com> - 0-3.8.git76fc0b3
- Updated dbus bindings to allow oci-register-machine to run on power machines

* Mon Jun 26 2017 Daniel Walsh <dwalsh@redhat.com> - 0-3.8.gitbf6b0f2
- oci-register-machine will not terminate containers with ID > 32 chars

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-3.7.gitbb20b00
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Oct 17 2016 Daniel Walsh <dwalsh@redhat.com> - 0-2-6.git7d4ce65
- Do not error out on TerminateMachine, if the machine no longer exists.

* Wed Aug 24 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-2.6.gitda32bb8e
- golang(gopkg.in/yaml.v1) is unbundled

* Wed Aug 24 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-2.5.gitda32bb8e
- bump to commit a32bb8e
- add dependency on golang(gopkg.in/yaml.v1)

* Mon Aug 22 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-2.4.git352a2a2
- bump to commit 352a2a2

* Thu Jul 21 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0-2.3.git31bbcd2
- https://fedoraproject.org/wiki/Changes/golang1.7

* Tue Jun 28 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-1.3.git31bbcd2
- use latest commit (builds successfully for RHEL)

* Thu Jun 23 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-1.2.git7d4ce65
- spec cleanup

* Wed Apr 20 2016 Daniel Walsh <dwalsh@redhat.com> - 0-1-1.git7d4ce65
- Add requires for systemd-machined systemd unit file

* Sat Mar 26 2016 Daniel Walsh <dwalsh@redhat.com> - 1-0.2.git7d4ce65
-  Fix logging format patch from Andy Goldstein

* Mon Feb 22 2016 Daniel Walsh <dwalsh@redhat.com> - 1-0.1
- Initial Release

* Thu Nov 19 2015 Sally O'Malley <somalley@redhat.com> - 0-0.1.git6863
- First package for Fedora
