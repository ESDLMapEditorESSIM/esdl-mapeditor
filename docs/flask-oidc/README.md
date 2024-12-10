# Flask-OIDC data

The new flask-oidc package has a different API to get data from the ID and Access JWT tokens.
For reference the following example data is present in the `session['oidc_auth_token']` variable:

```json
{
	"access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSld bla bla",
	"expires_in": 300,
	"refresh_expires_in": 1800,
	"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5c bla bla",
	"token_type": "bearer",
	"id_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA bla bla",
	"not-before-policy": 1713798074,
	"session_state": "10b73bc8-9826-4696-9c08-b8ebab2fc332",
	"scope": "openid user_group_path email profile esdl-mapeditor microprofile-jwt user_group essim",
	"expires_at": 1720525942,
	"userinfo": {
		"jti": "39fa12c1-a975-4404-ad93-9e014625691e",
		"exp": 1720525942,
		"nbf": 0,
		"iat": 1720525642,
		"iss": "https://idm.hesi.energy/auth/realms/esdl-mapeditor",
		"aud": "esdl-mapeditor",
		"sub": "bea2261d-6fdd-4061-9cf6-b2d8277580f0",
		"typ": "ID",
		"azp": "esdl-mapeditor",
		"nonce": "VbsjFaSd3qok94BYTISj",
		"auth_time": 1720525641,
		"session_state": "10b73bc8-9826-4696-9c08-b8ebab2fc332",
		"acr": "1",
		"esdl-drive-read-only": [
			"/Projects/Shared Models"
		],
		"user_group": [
			"development",
			"EIGEN",
			"Energie en Ruimte",
			"ESSIM-KPI test",
			"Go-E",
			"MCS",
			"Mondaine",
			"NieuweWarmteNu",
			"North Sea Energy",
			"Pocityf",
			"Public",
			"Public",
			"SeedERP - Energy modelling",
			"Shared Models",
			"Synergys",
			"Test group",
			"WarmingUp"
		],
		"resource_access": {
			"realm-management": {
				"roles": [
					"manage-users",
					"view-users",
					"query-groups",
					"query-users"
				]
			},
			"edr": {
				"roles": [
					"admin"
				]
			},
			"esdl-mapeditor": {
				"roles": [
					"mapeditor-admin"
				]
			},
			"cdo-mondaine": {
				"roles": [
					"esdl-drive-admin",
					"edr-public-write"
				]
			},
			"account": {
				"roles": [
					"manage-account",
					"manage-account-links",
					"view-profile"
				]
			}
		},
		"email_verified": "True",
		"role": "essim,geis,loadflow,urban-strategy,table,ibis,genemuiden,nzkg,ielgas,eps,test,opera,spatial,windcostmodel,service_area_service",
		"groups": [
			"edr_write_access",
			"offline_access",
			"cdo_read",
			"uma_authorization"
		],
		"preferred_username": "ewoud.werkman@tno.nl",
		"given_name": "Ewoud",
		"esdl-drive-write": [
			"/Projects/Shared Models"
		],
		"upn": "ewoud.werkman@tno.nl",
		"name": "Ewoud Werkman",
		"user_group_path": [
			"/Projects/development",
			"/Projects/EIGEN",
			"/Projects/Energie en Ruimte",
			"/Projects/ESSIM-KPI test",
			"/Projects/Go-E",
			"/Organizations/TNO/MCS",
			"/Projects/Mondaine",
			"/Projects/NieuweWarmteNu",
			"/Projects/North Sea Energy",
			"/Projects/Pocityf",
			"/edr/Public",
			"/Public",
			"/Projects/SeedERP - Energy modelling",
			"/Projects/Shared Models",
			"/Projects/Synergys",
			"/Test group",
			"/Projects/WarmingUp"
		],
		"family_name": "Werkman",
		"email": "ewoud.werkman@tno.nl"
	}
}
```

And the following data is present in the `user.profile` where `user: User = g.oidc_user`:
```json
{
	"esdl-drive-read-only": [
		"/Projects/Shared Models"
	],
	"sub": "bea2261d-6fdd-4061-9cf6-b2d8277580f0",
	"user_group": [
		"development",
		"EIGEN",
		"Energie en Ruimte",
		"ESSIM-KPI test",
		"Go-E",
		"MCS",
		"Mondaine",
		"NieuweWarmteNu",
		"North Sea Energy",
		"Pocityf",
		"Public",
		"Public",
		"SeedERP - Energy modelling",
		"Shared Models",
		"Synergys",
		"Test group",
		"WarmingUp"
	],
	"email_verified": "True",
	"role": "essim,geis,loadflow,urban-strategy,table,ibis,genemuiden,nzkg,ielgas,eps,test,opera,spatial,windcostmodel,service_area_service",
	"groups": [
		"edr_write_access",
		"offline_access",
		"cdo_read",
		"uma_authorization"
	],
	"preferred_username": "ewoud.werkman@tno.nl",
	"given_name": "Ewoud",
	"esdl-drive-write": [
		"/Projects/Shared Models"
	],
	"upn": "ewoud.werkman@tno.nl",
	"name": "Ewoud Werkman",
	"user_group_path": [
		"/Projects/development",
		"/Projects/EIGEN",
		"/Projects/Energie en Ruimte",
		"/Projects/ESSIM-KPI test",
		"/Projects/Go-E",
		"/Organizations/TNO/MCS",
		"/Projects/Mondaine",
		"/Projects/NieuweWarmteNu",
		"/Projects/North Sea Energy",
		"/Projects/Pocityf",
		"/edr/Public",
		"/Public",
		"/Projects/SeedERP - Energy modelling",
		"/Projects/Shared Models",
		"/Projects/Synergys",
		"/Test group",
		"/Projects/WarmingUp"
	],
	"family_name": "Werkman",
	"email": "ewoud.werkman@tno.nl"
}
```