%if %{_use_internal_dependency_generator}
%define __noautoprov 'perl(.*)'
%define __noautoreq 'perl\\(XML::Twig\\)|perl\\(MIME::Parser\\)|perl\\(Bugzilla.*\\)|perl\\(DBD::.*\\)|perl\\(DBI::st\\)|perl\\(DBI::db\\)|perl\\(TheSchwartz\\)'
%else
%define _provides_exceptions perl(.*)
%define _requires_exceptions perl(\\(XML::Twig\\|MIME::Parser\\|Bugzilla.*\\|DBD::.*\\|DBI::st\\))
%endif

Name:		bugzilla
Version:	4.0.1
Release:	8

Summary:	A bug tracking system developed by mozilla.org
License:	MPL
Group:		Networking/WWW
Url:		http://www.bugzilla.org
Source0:	ftp://ftp.mozilla.org/pub/mozilla.org/webtools/%{name}-%{version}.tar.gz
Patch0:		%{name}-3.6.3-fhs.patch
Patch1:		%{name}-4.0.1-dont-mess-file-perms.patch
# https://bugzilla.mozilla.org/show_bug.cgi?id=392482
Patch2:		%{name}-3.6-extern-id.patch
Requires:	apache
Requires:	perl(CGI) >= 1:3.500.0
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

# only install english templates (bug #61555)
install -d -m 755 %{buildroot}%{_datadir}/%{name}/template
cp -pr template/en %{buildroot}%{_datadir}/%{name}/template

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
    Require all granted

    Options ExecCGI
    DirectoryIndex index.cgi
</Directory>

# The duplicates.rdf must be accessible, as it is used by
# duplicates.xul
<Directory %{_localstatedir}/lib/bugzilla>
    <Files duplicates.rdf>
        Require all granted
    </Files>
</Directory>

# The dot files must be accessible to the public webdot server
# The png files locally created locally must be accessible
<Directory %{_localstatedir}/lib/bugzilla/webdot>
    <FilesMatch \.dot$>
        Require host research.att.com
    </FilesMatch>

    <FilesMatch \.png$>
        Require all granted
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


%changelog
* Thu Jun 16 2011 Guillaume Rousse <guillomovitch@mandriva.org> 4.0.1-1mdv2011.0
+ Revision: 685608
- new version

* Sun Feb 27 2011 Funda Wang <fwang@mandriva.org> 4.0-2
+ Revision: 640424
- rebuild to obsolete old packages

* Fri Feb 18 2011 Oden Eriksson <oeriksson@mandriva.com> 4.0-1
+ Revision: 638460
- 4.0
- rediff the mdv patches

* Sun Jan 30 2011 Guillaume Rousse <guillomovitch@mandriva.org> 3.6.4-1
+ Revision: 634176
- update to new version 3.6.4

  + Nicolas Lécureuil <nlecureuil@mandriva.com>
    - Update perl-CGI requires because of a security issue
      https://bugzilla.mozilla.org/show_bug.cgi?id=600464

* Sun Nov 07 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.6.3-2mdv2011.0
+ Revision: 594829
- only ship english templates (bug #61555)

* Sat Nov 06 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.6.3-1mdv2011.0
+ Revision: 594273
- new version
  update fhs and installation patches

* Wed Aug 11 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.6.2-1mdv2011.0
+ Revision: 569161
- new version

* Tue Apr 13 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.6-1mdv2010.1
+ Revision: 534573
- new version

* Thu Mar 18 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.6-1mdv2010.1
+ Revision: 525137
- update to new version 3.4.6

* Mon Mar 01 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.5-2mdv2010.1
+ Revision: 513138
- fix dependencies

* Sat Feb 06 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.5-1mdv2010.1
+ Revision: 501371
- new version

* Wed Jan 20 2010 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.4-2mdv2010.1
+ Revision: 494305
- switch to open to all by default, as the application does not allow modification of system state
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise

* Fri Dec 04 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.4-1mdv2010.1
+ Revision: 473485
- new version
- better apache configuration

* Mon Nov 30 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.3-2mdv2010.1
+ Revision: 472099
- restrict default access permissions to localhost only, as per new policy

* Sat Nov 07 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.3-1mdv2010.1
+ Revision: 462364
- update to new version 3.4.3

* Sun Sep 13 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.2-1mdv2010.0
+ Revision: 438635
- new version

* Wed Aug 19 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4.1-1mdv2010.0
+ Revision: 418278
- new version

* Wed Aug 12 2009 Jérôme Quelin <jquelin@mandriva.org> 3.4-3mdv2010.0
+ Revision: 415676
- adding security patch

* Wed Aug 12 2009 Jérôme Quelin <jquelin@mandriva.org> 3.4-2mdv2010.0
+ Revision: 415671
- bug 52827: adding missing requires:

* Tue Jul 28 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.4-1mdv2010.0
+ Revision: 402836
- new version

* Thu Jul 16 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.2.4-1mdv2010.0
+ Revision: 396682
- new version
- move all web files under %%{_datadir}/%%{name}/www

* Tue May 05 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.2.3-2mdv2010.0
+ Revision: 372202
- add soft dependencies for optional additional packages

* Thu Apr 02 2009 Guillaume Rousse <guillomovitch@mandriva.org> 3.2.3-1mdv2009.1
+ Revision: 363522
- update to new version 3.2.3

* Tue Feb 03 2009 Funda Wang <fwang@mandriva.org> 3.2.2-1mdv2009.1
+ Revision: 337090
- New version 3.2.2

* Fri Dec 05 2008 Guillaume Rousse <guillomovitch@mandriva.org> 3.2-1mdv2009.1
+ Revision: 310742
- new version
- rediff FHS and file perms patches

* Sun Nov 09 2008 Guillaume Rousse <guillomovitch@mandriva.org> 3.0.6-1mdv2009.1
+ Revision: 301431
- update to new version 3.0.6

* Mon Aug 25 2008 Funda Wang <fwang@mandriva.org> 3.0.5-1mdv2009.0
+ Revision: 275951
- rediff perms patch
- New version 3.0.5

* Thu Aug 07 2008 Thierry Vignaud <tv@mandriva.org> 3.0.4-2mdv2009.0
+ Revision: 266423
- rebuild early 2009.0 package (before pixel changes)

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Tue May 06 2008 Funda Wang <fwang@mandriva.org> 3.0.4-1mdv2009.0
+ Revision: 201767
- New version 3.0.4

* Fri Feb 29 2008 Guillaume Rousse <guillomovitch@mandriva.org> 3.0.3-1mdv2008.1
+ Revision: 176726
- update to new version 3.0.3

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Fri Dec 07 2007 Oden Eriksson <oeriksson@mandriva.com> 3.0.2-2mdv2008.1
+ Revision: 116252
- added P2 to be able to use apache-mod_authn_bugzilla

* Fri Nov 02 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0.2-1mdv2008.1
+ Revision: 105255
- new version

* Tue Sep 18 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0.1-2mdv2008.0
+ Revision: 89581
- rebuild

* Fri Aug 31 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0.1-1mdv2008.0
+ Revision: 77124
- new version
  drop duplicate warning patch (merged upstream)
  rediff fhs patch

* Wed May 30 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0-4mdv2008.0
+ Revision: 32946
- really fix dependencies, using individual module syntax rather than packages

* Fri May 25 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0-3mdv2008.0
+ Revision: 31125
- fix dependencies

* Thu May 24 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0-2mdv2008.0
+ Revision: 30905
- update dependencies
- fix alias ordering in apache configuration
- add missing custom skins directory
- fix FHS patch

* Thu May 17 2007 Guillaume Rousse <guillomovitch@mandriva.org> 3.0-1mdv2008.0
+ Revision: 27603
- new version


* Wed Feb 14 2007 Guillaume Rousse <guillomovitch@mandriva.org> 2.22.2-1mdv2007.0
+ Revision: 121057
- new version
  rediff FHS patch

* Thu Dec 14 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.22.1-1mdv2007.1
+ Revision: 96801
- new version
- Import bugzilla

* Sat Jul 01 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.22-4mdv2007.0
- relax buildrequires versionning

* Tue Jun 27 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.22-3mdv2007.0
- use new webapps macros
- don't provides private perl dependencies
- decompress all patches

* Tue May 23 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.22-2mdk
- fix apache configuration file backportability

* Wed May 10 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.22-1mdk
- new release
- buildrequires apache >= 2.0.54-5mdk because of macros use
- rediff FHS patch
- don't use backup files for patches, as it interferes with installed files

* Tue Apr 18 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.20.1-1mdk
- New release 2.20.1
- use herein document to manage README.mdv instead of additional source
- backport compatible apache configuration file
- mark the cron task as configuration to allow user customizations

* Mon Dec 05 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.20-2mdk
- misc fixes from Sherwin Daganato (<win@email.com.ph>)
 - rediff fhs patch to fix missed files
 - add whine.pl (new in v2.20) in cron and bindir
 - fix requires
 - fix regex in _requires_exceptions
- don't ship tests
- filter additional automatics requires
- drop require on perl-DBD-Mysql, bugzilla is supposed to be DB-agnostic now
- fix checksetup.pl path in README

* Sun Nov 06 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.20-1mdk
- 2.20
- use webapp rpm macros
- rediff all patches

* Fri Sep 23 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.18.3-1mdk
- new version 
- %%mkrel
- fix requires for contrib package

* Fri Jul 29 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.18.1-3mdk 
- requires sendmail-command

* Thu Jun 23 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.18.1-2mdk 
- new apache setup 
- clean apache config from useless directives
- update README.mdk
- more exceptions for handling optional packages

* Fri May 13 2005 Oden Eriksson <oeriksson@mandriva.com> 2.18.1-1mdk
- 2.18.1 (Minor bugfixes)
- rediffed P0

* Sat Apr 02 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.18-4mdk 
- ship configuration directory (thanks snt)

* Sat Feb 19 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.18-3mdk 
- patch files instead of setting PERL5LIB as bugzilla run in tainted mode
- more complete apache configuration
- update README.mdk
- make cron tasks run by apache user
- install tests and contribs
- ship contrib in a distinct subpackage

* Fri Feb 18 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.18-2mdk
- spec file cleanups, remove the ADVX-build stuff

* Thu Jan 27 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.18-1mdk 
- new version
- top-level is now /var/www/bugzilla
- non-accessible files are now in /usr/share/bugzilla
- herein document whenever possible
- no more order for apache configuration
- reload apache instead of restart it
- don't tag executables in /etc as executables
- README.mdk

* Mon Jan 17 2005 Stefan van der Eijk <stefan@mandrake.org> 2.16.8-1mdk
- New release 2.16.8

* Thu Jan 06 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.16.7-2mdk 
- fixed missing perl deps (thx knocte <knocte@gmail.com>)

* Mon Dec 06 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.16.7-1mdk
- 2.16.7 (security and bugfixes release)

* Tue Jul 20 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.16.6-2mdk 
- apache config file in /etc/httpd/webapps.d
- standard perms for /etc/httpd/webapps.d/%%{order}_bugzilla.conf

* Mon Jul 12 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.16.6-1mdk
- 2.16.6 (minor bugfixes)

* Fri Apr 23 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.16.5-1mdk
- new version
- dropped useless provides
- rpmbuildupdate aware

* Tue Apr 13 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.16.4-3mdk
- updated description (John Keller <jkeller@matchbox.fr>)

* Wed Apr 07 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.16.4-2mdk
- let spechelper compute perl dependencies

