6.0
===

Switch to pkgutil-style namespace package.

5.5
===

Refresh package metadata.

5.4.2
=====

Fix regressions in 5.4.1 where short hashes and detached tags
were no longer suitable revisions for Repo.update.

5.4.1
=====

Fix issue with git-pulling revisions.

Allow "rev" to be None, in which case, default to master or tip.

5.4
===

Swarm model can be used in sets and comparable.
BaseResource has by_id classmethod.

5.3
===

#3: Add functionality to Ingredient model.

5.1
===

In Velociraptor.get_credentials, allow username and password
to be resolved by environment variables.

5.0
===

Removed ``utc`` and ``utcfromtimestamp`` from ``common.utils``.
Use ``utc.UTC`` and ``utc.fromtimestamp`` from the `utc
<https://pypi.org/project/utc>`_ instead.

``vr.common.paths`` no longer exposes ``ProcData``, which should
be imported from ``vr.common.models``.

4.10
====

Add suds-py3 as a dependency when on Python 3.

Added new 'balancers' extra, which installs the dependencies for
the balancers.

4.9.2
=====

Clean empty pools in StingRay balancer

4.9.1
=====

Remove dependency to SetuptoolsVersion

4.9
===

Make overlayfs configuration dependent on LXC

4.8.2
=====

Fixed ImportError in 'vr.common.balancer.varnish'.

4.8
===

Moved project to Github.

Incorporated `project
skeleton from jaraco <https://github.com/jaraco/skeleton>`_.
Enabled automatic releases of tagged commits.

4.6.1
=====

Fix QueryResult iterability on Python 3.

4.6
===

In models, allow parameters to be supplied when loading
entities.

4.5
===

Nicer error reporting in Velociraptor client when credentials are
invalid.

4.0
===

Installation now requires pip 6.x or later.
