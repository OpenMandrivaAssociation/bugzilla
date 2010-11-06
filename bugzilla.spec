%define name	bugzilla
%define version 3.6.3
%define release %mkrel 1

%define _provides_exceptions perl(.*)
%define _requires_exceptions perl(\\(XML::Twig\\|MIME::Parser\\|Bugzilla.*\\|DBD::.*\\|DBI::st\\))

Name:		%{name}
Version:	%{version}
Release:	%{release}

Summary:	A bug tracking system developed by mozilla.org
License:	MPL
Group:		Networking/WWW
Url:		http://www.bugzilla.org
Source0:	ftp://ftp.mozilla.org/pub/mozilla.org/webtools/%{name}-%{version}.tar.gz
Patch0:		%{name}-3.6.3-fhs.patch
Patch1:		%{name}-3.6.3-dont-mess-file-perms.patch
# https://bugzilla.mozilla.org/show_bug.cgi?id=392482
Patch2:		%{name}-3.6-extern-id.patch
Requires:	apache
Requires:	perl(CGI) >= 2.93
Requires:	perl(Date::Format) >= 2.21
Requires:	perl(DateTime)     >= 0.280.0
Requires:	perl(Digest::SHA)
Requires:	perl(File::Spec)   >= 0.840.0
Requires:	perl(DBI)          >= 1.410.0
Requires:	perl(Template)     >= 2.120.0
Requires:	perl(Email::Send)  >= 2.0.0
Requires:	perl(Email::MIME::Modifier)
Requires:	sendmail-command
%if %mdkversion < 201010
Requires(post):   rpm-helper
Requires(postun):   rpm-helper
%endif
Suggests: diffutils
Suggests: graphviz
Suggests: patchutils
Suggests: perl(DBD::mysql) >= 4.0.0
Suggests: perl(DBD::Pg)    >= 1.45.0
Suggests: perl(GD)
Suggests: perl(GD::Graph)
Suggests: perl(GD::TextUtil)
Suggests: perl(Chart::Base)
Suggests: perl(Net::LDAP)
Suggests: perl(PatchReader)
Suggests: perl(XML::Parser)
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}

%description
Bugzilla is one example of a class of programs called "Defect Tracking
Systems", or, more commonly, "Bug-Tracking Systems". Defect Tracking Systems
allow individual or groups of developers to keep track of outstanding bugs
in their product effectively.

%package contrib
Summary:	Additional tools for %{name}
Group:		Networking/WWW

%description contrib
This package contains additional tools for %{name}.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1
find . -name CVS -o -name .cvsignore | xargs rm -rf

# fix perms
chmod -R go=u-w .
chmod 644 Bugzilla/Bug.pm
chmod 644 template/en/default/admin/keywords/*
chmod 755 docs/makedocs.pl

# fix paths
find . -type f | xargs perl -pi -e "s|/usr/local/bin|%{_bindir}|g"

# fix contrib documentation files names
(cd contrib/bugzilla-submit && mv README README.bugzilla-submit)

%build

%install
rm -rf %{buildroot}

install -d -m 755 %{buildroot}%{_datadir}/%{name}

install -d -m 755 %{buildroot}%{_datadir}/%{name}/www
install -m 755 *.cgi %{buildroot}%{_datadir}/%{name}/www
cp -pr js skins images robots.txt %{buildroot}%{_datadir}/%{name}/www
install -d -m 755 %{buildroot}%{_datadir}/%{name}/extensions
install -d -m 755 %{buildroot}%{_datadir}/%{name}/www/skins/custom
install -d -m 755 %{buildroot}%{_datadir}/%{name}/www/skins/contrib

install -d -m 755 %{buildroot}%{_datadir}/%{name}/lib
install -d -m 755 %{buildroot}%{_datadir}/%{name}/bin
cp -pr template %{buildroot}%{_datadir}/%{name}
cp -pr Bugzilla %{buildroot}%{_datadir}/%{name}/lib
install -m 644 Bugzilla.pm \
	%{buildroot}%{_datadir}/%{name}/lib
install -m 755 collectstats.pl \
	testserver.pl \
	checksetup.pl \
	importxml.pl \
	whineatnews.pl \
	whine.pl \
	contrib/bugzilla_ldapsync.rb \
	contrib/bzdbcopy.pl \
	contrib/cvs-update.pl \
	contrib/jb2bz.py \
	contrib/merge-users.pl \
	contrib/mysqld-watcher.pl \
	contrib/sendbugmail.pl \
	contrib/sendunsentbugmail.pl \
	contrib/syncLDAP.pl \
	contrib/yp_nomail.sh \
	contrib/bugzilla-submit/bugzilla-submit \
	contrib/cmdline/buglist \
	contrib/cmdline/bugs \
	%{buildroot}%{_datadir}/%{name}/bin
cp -p bugzilla.dtd %{buildroot}%{_datadir}/%{name}

install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
install -m 644 contrib/cmdline/query.conf %{buildroot}%{_sysconfdir}/%{name}

install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}

# apache configuration
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Bugzilla Apache configuration
Alias /bugzilla/data %{_localstatedir}/lib/bugzilla/
Alias /%{name} %{_datadir}/%{name}/www

<Directory %{_datadir}/%{name}/www>
    Order allow,deny
    Allow from all

    Options ExecCGI
    DirectoryIndex index.cgi
</Directory>

# The duplicates.rdf must be accessible, as it is used by
# duplicates.xul
<Directory %{_localstatedir}/lib/bugzilla>
    <Files duplicates.rdf>
        Order allow,deny
        Allow from all
    </Files>
</Directory>

# The dot files must be accessible to the public webdot server
# The png files locally created locally must be accessible
<Directory %{_localstatedir}/lib/bugzilla/webdot>
    <FilesMatch \.dot$>
        Order deny,allow
        Deny from all
        Allow from research.att.com
    </FilesMatch>

    <FilesMatch \.png$>
        Order allow,deny
        Allow from all
    </FilesMatch>
</Directory>
EOF

# cron task
install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name} <<EOF
0 0 * * *     apache     %{_datadir}/%{name}/bin/collectstats.pl > /dev/null 2>&1
0 0 * * *     apache     %{_datadir}/%{name}/bin/whineatnews.pl > /dev/null 2>&1
*/15 * * * *     apache     %{_datadir}/%{name}/bin/whine.pl > /dev/null 2>&1
EOF

cat > README.mdv <<EOF
Mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- the constant files are in %{_datadir}/%{name}
- the variables files are in %{_localstatedir}/lib/%{name}
- the configuration file will be generated in %{_sysconfdir}/%{name}

post-installation
-----------------
You have to create the MySQL database, and run %{_datadir}/%{name}/bin/checksetup.pl

Additional useful packages
--------------------------
- perl-GD, perl-GDGraph, perl-GD-TextUtil and perl-Chart for graphical reports
- perl-XML-Parser for importing XML bugs
- perl-Net-LDAP for LDAP authentication
- perl-PatchReader, cvs, diffutils and patchutils for patch viewer
- graphviz for graphical view of dependency relationships
- a MySQL database, either locale or remote
EOF

%clean
rm -rf %{buildroot}

%post
%if %mdkversion < 201010
%_post_webapp
%endif

%postun
%if %mdkversion < 201010
%_postun_webapp
%endif

%files
%defattr(-,root,root)
%doc README README.mdv docs
%config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/cron.d/%{name}
%{_datadir}/%{name}
%{_sysconfdir}/%{name}
%attr(-,apache,apache) %{_localstatedir}/lib/%{name}
%exclude %{_datadir}/%{name}/bin/bugzilla_ldapsync.rb
%exclude %{_datadir}/%{name}/bin/cvs-update.pl
%exclude %{_datadir}/%{name}/bin/jb2bz.py
%exclude %{_datadir}/%{name}/bin/mysqld-watcher.pl
%exclude %{_datadir}/%{name}/bin/sendbugmail.pl
%exclude %{_datadir}/%{name}/bin/sendunsentbugmail.pl
%exclude %{_datadir}/%{name}/bin/syncLDAP.pl
%exclude %{_datadir}/%{name}/bin/yp_nomail.sh
%exclude %{_datadir}/%{name}/bin/bugzilla-submit
%exclude %{_datadir}/%{name}/bin/buglist
%exclude %{_datadir}/%{name}/bin/bugs
%exclude %{_sysconfdir}/%{name}/query.conf

%files contrib
%defattr(-,root,root)
%doc contrib/README
%doc contrib/bugzilla-submit/README.bugzilla-submit
%{_datadir}/%{name}/bin/bugzilla_ldapsync.rb
%{_datadir}/%{name}/bin/cvs-update.pl
%{_datadir}/%{name}/bin/jb2bz.py
%{_datadir}/%{name}/bin/mysqld-watcher.pl
%{_datadir}/%{name}/bin/sendbugmail.pl
%{_datadir}/%{name}/bin/sendunsentbugmail.pl
%{_datadir}/%{name}/bin/syncLDAP.pl
%{_datadir}/%{name}/bin/yp_nomail.sh
%{_datadir}/%{name}/bin/bugzilla-submit
%{_datadir}/%{name}/bin/buglist
%{_datadir}/%{name}/bin/bugs
%config(noreplace) %{_sysconfdir}/%{name}/query.conf
