--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: damage_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.damage_types (
    class_key character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    description text,
    model_label character varying(60),
    model_class_index integer,
    color_hex character varying(9),
    is_critical boolean NOT NULL,
    default_severity_rules jsonb,
    is_active boolean NOT NULL,
    sort_order integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.damage_types OWNER TO postgres;

--
-- Name: detections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detections (
    inspection_id uuid NOT NULL,
    inspection_image_id uuid NOT NULL,
    damage_type_id uuid NOT NULL,
    confidence numeric(5,4) NOT NULL,
    severity character varying(20) NOT NULL,
    bbox_x integer,
    bbox_y integer,
    bbox_width integer,
    bbox_height integer,
    polygon jsonb,
    area_ratio numeric(7,6),
    panel_hint character varying(60),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.detections OWNER TO postgres;

--
-- Name: inference_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inference_runs (
    inspection_id uuid NOT NULL,
    inspection_image_id uuid,
    model_backend character varying(40) NOT NULL,
    model_name character varying(100),
    model_version character varying(50),
    raw_output jsonb,
    duration_ms integer,
    attempt integer NOT NULL,
    succeeded boolean NOT NULL,
    error_detail text,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.inference_runs OWNER TO postgres;

--
-- Name: inspection_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inspection_images (
    inspection_id uuid NOT NULL,
    cloudinary_public_id character varying(255) NOT NULL,
    secure_url text NOT NULL,
    thumbnail_url text,
    view_angle character varying(20),
    width integer,
    height integer,
    file_size_bytes bigint,
    format character varying(10),
    sequence_no integer NOT NULL,
    status character varying(20) NOT NULL,
    failure_reason text,
    quality_report jsonb,
    annotated_url text,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.inspection_images OWNER TO postgres;

--
-- Name: inspections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inspections (
    user_id uuid NOT NULL,
    vehicle_id uuid,
    reference_code character varying(40) NOT NULL,
    status character varying(20) NOT NULL,
    overall_severity character varying(20) NOT NULL,
    damage_score integer NOT NULL,
    total_detections integer NOT NULL,
    image_count integer NOT NULL,
    total_area_percent double precision NOT NULL,
    damage_summary jsonb,
    model_name character varying(100),
    model_version character varying(50),
    processing_started_at timestamp with time zone,
    processing_completed_at timestamp with time zone,
    processing_ms integer,
    error_code character varying(60),
    error_message text,
    idempotency_key character varying(120),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    detection_preset character varying(20),
    detection_settings jsonb,
    below_threshold_count integer NOT NULL
);


ALTER TABLE public.inspections OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(150),
    phone character varying(20),
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vehicles (
    user_id uuid NOT NULL,
    registration_number character varying(30),
    make character varying(60),
    model character varying(60),
    year integer,
    colour character varying(40),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.vehicles OWNER TO postgres;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
7b3dfaf80e0e
\.


--
-- Data for Name: damage_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.damage_types (class_key, display_name, description, model_label, model_class_index, color_hex, is_critical, default_severity_rules, is_active, sort_order, id, created_at, updated_at) FROM stdin;
dent	Dent	Indentations, dings and sheet metal compressions.	dent	0	#38bdf8	f	\N	t	1	5dced117-c5b2-4be6-91fb-a076a6ce0d21	2026-08-18 11:55:27.002547+05:30	2026-08-18 11:55:27.002547+05:30
scratch	Scratch	Paint abrasions, scrape lines and clear-coat scuffs.	scratch	1	#f59e0b	f	\N	t	2	802cacb5-e296-4b62-8f5f-4fcbd34a6503	2026-08-18 11:55:27.007079+05:30	2026-08-18 11:55:27.007079+05:30
crack	Crack	Windshield fissures and bumper or fender cracks.	crack	2	#f43f5e	f	\N	t	3	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	2026-08-18 11:55:27.009079+05:30	2026-08-18 11:55:27.009079+05:30
glass_shatter	Glass Shatter	Webbed breaks and shattered window panels.	glass shatter	3	#c084fc	t	\N	t	4	a41cd314-1427-4003-a2b9-313216c56fd7	2026-08-18 11:55:27.010076+05:30	2026-08-18 11:55:27.010076+05:30
lamp_broken	Lamp Broken	Broken headlight, taillight or turn signal lenses.	lamp broken	4	#fde047	t	\N	t	5	252cd10c-eb2d-4a8c-ac32-28a5af142a74	2026-08-18 11:55:27.012079+05:30	2026-08-18 11:55:27.012079+05:30
tire_flat	Tire Flat	Deflated tyre, punctured sidewall or exposed rim.	tire flat	5	#34d399	t	\N	t	6	e4d231fc-562f-44f5-9f50-4e4c68c25266	2026-08-18 11:55:27.014076+05:30	2026-08-18 11:55:27.014076+05:30
\.


--
-- Data for Name: detections; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detections (inspection_id, inspection_image_id, damage_type_id, confidence, severity, bbox_x, bbox_y, bbox_width, bbox_height, polygon, area_ratio, panel_hint, id, created_at, updated_at) FROM stdin;
f11c86cf-10e4-4976-9770-354a48ee4188	058d673a-1b82-42c7-b9b0-f54eddc4369f	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.6048	severe	268	73	359	108	null	0.186770	\N	050ea9e5-3c0b-46e3-a228-76a82d763d54	2026-08-18 12:02:26.402377+05:30	2026-08-18 12:02:26.402377+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	137be88f-3711-4ad5-b8fc-f21d557ee651	a41cd314-1427-4003-a2b9-313216c56fd7	0.5898	severe	22	1	500	499	null	0.501342	\N	86bc7a1d-df40-4bff-90e6-b147759aba37	2026-08-18 12:02:30.616106+05:30	2026-08-18 12:02:30.616106+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	137be88f-3711-4ad5-b8fc-f21d557ee651	a41cd314-1427-4003-a2b9-313216c56fd7	0.5078	severe	438	12	424	545	null	0.464329	\N	6c76da4a-b703-4b6e-a481-6292bf87fbdf	2026-08-18 12:02:30.616106+05:30	2026-08-18 12:02:30.616106+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	cba4a5b6-f197-4569-93da-77bea6f4d53a	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.6048	severe	268	73	359	108	null	0.186770	\N	d12634c7-ce54-4ff4-9e2c-a76a6d580351	2026-08-18 12:04:55.950576+05:30	2026-08-18 12:04:55.950576+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	61c08572-1825-4c3c-9d1e-28fc6d0c7892	a41cd314-1427-4003-a2b9-313216c56fd7	0.5898	severe	22	1	500	499	null	0.501342	\N	c0acf772-d54c-4485-afd1-cbedab75db6e	2026-08-18 12:04:59.281399+05:30	2026-08-18 12:04:59.281399+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	61c08572-1825-4c3c-9d1e-28fc6d0c7892	a41cd314-1427-4003-a2b9-313216c56fd7	0.5078	severe	438	12	424	545	null	0.464329	\N	16eb9d47-9f91-4379-b7b7-3d5c95ca0440	2026-08-18 12:04:59.281399+05:30	2026-08-18 12:04:59.281399+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	d635b741-cbf2-42b5-b699-64dafae438bc	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.6048	severe	268	73	359	108	null	0.186770	\N	f517003c-116a-47ed-866f-3c5924b8f27b	2026-08-18 12:08:01.015771+05:30	2026-08-18 12:08:01.015771+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	ba5683f6-af06-498d-9e7b-7a7fda54c12b	a41cd314-1427-4003-a2b9-313216c56fd7	0.5898	severe	22	1	500	499	null	0.501342	\N	64acf019-d9f3-4178-a6eb-cc453ce789cd	2026-08-18 12:08:03.763669+05:30	2026-08-18 12:08:03.763669+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	ba5683f6-af06-498d-9e7b-7a7fda54c12b	a41cd314-1427-4003-a2b9-313216c56fd7	0.5078	severe	438	12	424	545	null	0.464329	\N	1234d6dc-6b73-4978-9b42-b953c928106b	2026-08-18 12:08:03.763669+05:30	2026-08-18 12:08:03.763669+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	b3c1425e-776f-40a7-81bc-ed57a2e56734	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.5712	severe	217	118	553	267	null	0.481663	\N	b2791078-2b00-4e9a-99a9-20ab0d6b3793	2026-08-18 12:44:59.966679+05:30	2026-08-18 12:44:59.966679+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	76aae949-89b9-4565-a491-c9ec44fb0923	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	2cd0f9a1-21b3-4669-86f5-f5512272ad73	2026-08-18 12:45:03.83497+05:30	2026-08-18 12:45:03.83497+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	\N	16177583-f52b-47db-9244-41f8f2a26973	2026-08-18 12:45:07.279655+05:30	2026-08-18 12:45:07.279655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	\N	5ea32ac7-3fdc-4a47-998a-83e7069c9f5f	2026-08-18 12:45:07.279655+05:30	2026-08-18 12:45:07.279655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	831c1497-13f3-4a93-818a-a1c50469cb97	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	\N	02f3b028-d76e-4c7d-8824-d06952c1cdc1	2026-08-18 12:45:10.510826+05:30	2026-08-18 12:45:10.510826+05:30
ba268fb6-dcf4-43c5-b75d-495f02f02e24	b3e19897-20fc-4adf-8ee2-3ce0b2fd9986	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.6395	severe	125	99	203	152	null	0.249194	\N	8e2e1842-7aab-4f9a-90ea-696340a293a6	2026-08-18 13:05:39.471468+05:30	2026-08-18 13:05:39.471468+05:30
ba268fb6-dcf4-43c5-b75d-495f02f02e24	b3e19897-20fc-4adf-8ee2-3ce0b2fd9986	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.5170	severe	144	4	189	119	null	0.181638	\N	e26cf38a-92b9-4f8c-a58f-45b071e050c9	2026-08-18 13:05:39.471468+05:30	2026-08-18 13:05:39.471468+05:30
ba268fb6-dcf4-43c5-b75d-495f02f02e24	b3e19897-20fc-4adf-8ee2-3ce0b2fd9986	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3909	severe	11	90	224	156	null	0.282209	\N	d0387773-0fc1-4aa8-be34-76984ad9100c	2026-08-18 13:05:39.471468+05:30	2026-08-18 13:05:39.471468+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	d0a2e6f1-e881-49c1-afc4-aea5eb300b14	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.6048	severe	763	256	1023	379	null	0.186770	\N	ecd2622a-dbd4-4c3b-b414-04213037a97a	2026-08-18 13:25:49.090847+05:30	2026-08-18 13:25:49.090847+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	13e9d380-3ce5-48ef-a0af-17d28878f3d3	a41cd314-1427-4003-a2b9-313216c56fd7	0.5898	severe	49	2	1111	936	null	0.501342	\N	fffd4b8e-4c7c-4f48-b18b-03f99986e169	2026-08-18 13:25:51.897093+05:30	2026-08-18 13:25:51.897093+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	13e9d380-3ce5-48ef-a0af-17d28878f3d3	a41cd314-1427-4003-a2b9-313216c56fd7	0.5078	severe	973	22	942	1022	null	0.464329	\N	d165f4fa-de6c-4495-9b3a-62e8ef39f0a2	2026-08-18 13:25:51.897093+05:30	2026-08-18 13:25:51.897093+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dadaa205-d762-4b55-883f-dce322cb3299	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3066	severe	267	124	462	198	null	0.298411	\N	ab999ade-2e6e-453f-b212-63fcc53c0fbb	2026-08-18 13:29:10.94124+05:30	2026-08-18 13:29:10.94124+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	d6278766-7304-420b-a936-f4e6c1d403c1	2026-08-18 13:29:13.869482+05:30	2026-08-18 13:29:13.869482+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	\N	18a70a98-174d-434b-9b88-a9adc5d54eea	2026-08-18 13:29:13.869482+05:30	2026-08-18 13:29:13.869482+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	209d7f94-3f02-4cbe-9179-f08b8f32821c	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	\N	e70b80bb-b87c-42b0-b5eb-d3c3a240d478	2026-08-18 13:29:16.760004+05:30	2026-08-18 13:29:16.760004+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	209d7f94-3f02-4cbe-9179-f08b8f32821c	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	\N	9ba0398f-01db-481d-bd2c-dc1047d40891	2026-08-18 13:29:16.760004+05:30	2026-08-18 13:29:16.760004+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	32152275-4ba8-4a3d-9f54-9abd4c09a271	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	\N	99626d99-ee0a-4f6a-8a1d-1f154f55bcee	2026-08-18 13:29:19.703733+05:30	2026-08-18 13:29:19.703733+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	32152275-4ba8-4a3d-9f54-9abd4c09a271	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3037	minor	148	409	97	42	null	0.013294	\N	55015128-5086-4385-9305-94f69e605e8a	2026-08-18 13:29:19.703733+05:30	2026-08-18 13:29:19.703733+05:30
074094a4-77af-408c-ab06-6eda073d3df8	b6b8ee05-8838-4f76-a97c-655f47d0d151	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	fc896b2c-0aac-4fd6-82bd-25c119efdda2	2026-08-18 13:31:33.941246+05:30	2026-08-18 13:31:33.941246+05:30
074094a4-77af-408c-ab06-6eda073d3df8	b6b8ee05-8838-4f76-a97c-655f47d0d151	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	\N	3bcc79d0-b4a7-4365-83d8-7417b5dd6894	2026-08-18 13:31:33.941246+05:30	2026-08-18 13:31:33.941246+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	610f294b-4b90-499a-8b32-93ddabe4ed6b	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	\N	1cc19474-4452-4a61-a846-1b27b5018dbc	2026-08-18 13:32:32.456464+05:30	2026-08-18 13:32:32.456464+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	a3e066b5-8aba-4e2d-be33-485ca76e361f	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	08ec4bf4-a71b-42ef-9e85-c1a9d3e6719c	2026-08-18 16:22:53.561988+05:30	2026-08-18 16:22:53.561988+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	d41fc5b7-4b31-4220-91a8-abd94c433865	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	\N	01b48011-c016-48bb-9912-19533cdbe5de	2026-08-18 16:22:57.975871+05:30	2026-08-18 16:22:57.975871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	d41fc5b7-4b31-4220-91a8-abd94c433865	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	\N	bb55b640-90e4-4959-b0ba-3b7c5248c38e	2026-08-18 16:22:57.975871+05:30	2026-08-18 16:22:57.975871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	4974153c-05e9-4171-84f2-6f950b163d22	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	\N	addd21f0-4e26-4be3-b8e9-d32ad7d0328b	2026-08-18 16:23:01.423813+05:30	2026-08-18 16:23:01.423813+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	0020b111-0adb-4e04-a807-b4fbe7226233	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3066	severe	267	124	462	198	null	0.298411	\N	0887fd89-0b02-431e-a1f8-406630e327d8	2026-08-18 16:27:44.364518+05:30	2026-08-18 16:27:44.364518+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	db644740-6b72-4998-adaa-52d04816f7f2	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	4711a599-10d7-4336-8031-9e9cfec09b76	2026-08-18 16:27:47.825149+05:30	2026-08-18 16:27:47.825149+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	db644740-6b72-4998-adaa-52d04816f7f2	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	\N	297c372d-c02d-4f2f-b07c-7aa379cd2383	2026-08-18 16:27:47.825149+05:30	2026-08-18 16:27:47.825149+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.8646	severe	0	152	616	415	null	0.243797	\N	8ad55e28-3dcb-4044-a574-d2b645eac76d	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.7152	severe	522	375	297	265	null	0.075059	\N	8d06f780-0de9-49e2-9b1c-8c9d7139573e	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.3973	minor	184	808	19	15	null	0.000272	\N	aca3e57e-49f8-473c-8484-148f33ca26c8	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.2807	minor	765	434	28	25	null	0.000668	\N	688c75d4-855c-4324-9e08-6a57ed22c7a2	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.2681	minor	240	797	28	29	null	0.000774	\N	d5852173-054d-4c8e-8d24-d7bcd02f1a4e	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	75bb6f49-597f-4630-bfe1-6b436744a217	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	\N	3a402584-adf8-42b7-971f-8c9db074efb1	2026-08-18 19:12:39.283719+05:30	2026-08-18 19:12:39.283719+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	049e1d42-6d2d-452f-9147-43ab3a616694	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	\N	4f408d67-061f-4415-9aec-538b8e90ae5f	2026-08-18 19:12:43.056949+05:30	2026-08-18 19:12:43.056949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	049e1d42-6d2d-452f-9147-43ab3a616694	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	\N	114f0a59-61f4-4ccf-b1a0-5ed19631a770	2026-08-18 19:12:43.056949+05:30	2026-08-18 19:12:43.056949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	e08d1eb7-ba4d-4a0a-b173-3e4b0d4f7d2b	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	\N	df1c69bb-4383-4121-a77b-402d2c7f4b04	2026-08-18 19:12:46.282382+05:30	2026-08-18 19:12:46.282382+05:30
\.


--
-- Data for Name: inference_runs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inference_runs (inspection_id, inspection_image_id, model_backend, model_name, model_version, raw_output, duration_ms, attempt, succeeded, error_detail, id, created_at, updated_at) FROM stdin;
64c0e21e-8228-4345-875d-5b3002a306cd	d635b741-cbf2-42b5-b699-64dafae438bc	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 38772, "bbox": {"x1": 268, "x2": 627, "y1": 73, "y2": 181}, "width": 359, "height": 108, "class_id": 1, "class_name": "scratch", "confidence": 0.6048, "area_percentage": 18.68, "confidence_percent": 60.5}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}, "detection_count": 1, "image_dimensions": {"width": 674, "height": 308}}	8923	1	t	\N	43b67124-8726-4154-8a7d-8b0de48e2452	2026-08-18 11:59:21.345219+05:30	2026-08-18 11:59:21.345219+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	ba5683f6-af06-498d-9e7b-7a7fda54c12b	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 249500, "bbox": {"x1": 22, "x2": 522, "y1": 1, "y2": 500}, "width": 500, "height": 499, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5898, "area_percentage": 50.13, "confidence_percent": 59.0}, {"area": 231080, "bbox": {"x1": 438, "x2": 862, "y1": 12, "y2": 557}, "width": 424, "height": 545, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5078, "area_percentage": 46.43, "confidence_percent": 50.8}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}, "detection_count": 2, "image_dimensions": {"width": 864, "height": 576}}	2983	1	t	\N	44f25f15-4030-4b0d-9974-06e57932ad3f	2026-08-18 11:59:25.452429+05:30	2026-08-18 11:59:25.452429+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	058d673a-1b82-42c7-b9b0-f54eddc4369f	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 38772, "bbox": {"x1": 268, "x2": 627, "y1": 73, "y2": 181}, "width": 359, "height": 108, "class_id": 1, "class_name": "scratch", "confidence": 0.6048, "area_percentage": 18.68, "confidence_percent": 60.5}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}, "detection_count": 1, "image_dimensions": {"width": 674, "height": 308}}	6535	1	t	\N	641df157-2645-4d1c-83c2-bfb4badd8477	2026-08-18 12:02:26.400378+05:30	2026-08-18 12:02:26.400378+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	137be88f-3711-4ad5-b8fc-f21d557ee651	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 249500, "bbox": {"x1": 22, "x2": 522, "y1": 1, "y2": 500}, "width": 500, "height": 499, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5898, "area_percentage": 50.13, "confidence_percent": 59.0}, {"area": 231080, "bbox": {"x1": 438, "x2": 862, "y1": 12, "y2": 557}, "width": 424, "height": 545, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5078, "area_percentage": 46.43, "confidence_percent": 50.8}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}, "detection_count": 2, "image_dimensions": {"width": 864, "height": 576}}	4078	1	t	\N	3a982d82-0374-4a73-a6b9-51a0c87ce660	2026-08-18 12:02:30.613107+05:30	2026-08-18 12:02:30.613107+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	cba4a5b6-f197-4569-93da-77bea6f4d53a	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 38772, "bbox": {"x1": 268, "x2": 627, "y1": 73, "y2": 181}, "width": 359, "height": 108, "class_id": 1, "class_name": "scratch", "confidence": 0.6048, "area_percentage": 18.68, "confidence_percent": 60.5}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}, "detection_count": 1, "image_dimensions": {"width": 674, "height": 308}}	9341	1	t	\N	0d45ed68-37f3-4520-8637-116941e0c66b	2026-08-18 12:04:55.941572+05:30	2026-08-18 12:04:55.941572+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	61c08572-1825-4c3c-9d1e-28fc6d0c7892	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 249500, "bbox": {"x1": 22, "x2": 522, "y1": 1, "y2": 500}, "width": 500, "height": 499, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5898, "area_percentage": 50.13, "confidence_percent": 59.0}, {"area": 231080, "bbox": {"x1": 438, "x2": 862, "y1": 12, "y2": 557}, "width": 424, "height": 545, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5078, "area_percentage": 46.43, "confidence_percent": 50.8}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}, "detection_count": 2, "image_dimensions": {"width": 864, "height": 576}}	3201	1	t	\N	ef1a312e-f5c5-45a4-9698-6695d9975807	2026-08-18 12:04:59.277399+05:30	2026-08-18 12:04:59.277399+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	d635b741-cbf2-42b5-b699-64dafae438bc	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 38772, "bbox": {"x1": 268, "x2": 627, "y1": 73, "y2": 181}, "width": 359, "height": 108, "class_id": 1, "class_name": "scratch", "confidence": 0.6048, "area_percentage": 18.68, "confidence_percent": 60.5}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}, "detection_count": 1, "image_dimensions": {"width": 674, "height": 308}}	4673	1	t	\N	cac9a18b-3df8-4cd1-b5f4-f653aff2aa1e	2026-08-18 12:08:01.010765+05:30	2026-08-18 12:08:01.010765+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	ba5683f6-af06-498d-9e7b-7a7fda54c12b	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 249500, "bbox": {"x1": 22, "x2": 522, "y1": 1, "y2": 500}, "width": 500, "height": 499, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5898, "area_percentage": 50.13, "confidence_percent": 59.0}, {"area": 231080, "bbox": {"x1": 438, "x2": 862, "y1": 12, "y2": 557}, "width": 424, "height": 545, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5078, "area_percentage": 46.43, "confidence_percent": 50.8}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}, "detection_count": 2, "image_dimensions": {"width": 864, "height": 576}}	2614	1	t	\N	47834cba-9d2c-4b98-b12d-650df45f4ac3	2026-08-18 12:08:03.761667+05:30	2026-08-18 12:08:03.761667+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	b3c1425e-776f-40a7-81bc-ed57a2e56734	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 147651, "bbox": {"x1": 217, "x2": 770, "y1": 118, "y2": 385}, "width": 553, "height": 267, "class_id": 1, "class_name": "scratch", "confidence": 0.5712, "area_percentage": 48.17, "confidence_percent": 57.1}, {"area": 11235, "bbox": {"x1": 657, "x2": 764, "y1": 96, "y2": 201}, "width": 107, "height": 105, "class_id": 2, "class_name": "crack", "confidence": 0.3288, "area_percentage": 3.67, "confidence_percent": 32.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.1925, "clahe": false, "imgsz": 1024, "fallback_pass_used": true}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	12480	1	t	\N	31102d75-959c-4f84-9b12-f4dfab141641	2026-08-18 12:44:59.947678+05:30	2026-08-18 12:44:59.947678+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	76aae949-89b9-4565-a491-c9ec44fb0923	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "area_percentage": 21.51, "confidence_percent": 47.2}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 1, "image_dimensions": {"width": 1024, "height": 703}}	2717	1	t	\N	730bf6ad-2748-4238-8a40-d176a1a4af38	2026-08-18 12:45:03.830966+05:30	2026-08-18 12:45:03.830966+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 648, "bbox": {"x1": 285, "x2": 303, "y1": 81, "y2": 117}, "width": 18, "height": 36, "class_id": 2, "class_name": "crack", "confidence": 0.6132, "area_percentage": 0.32, "confidence_percent": 61.3}, {"area": 26264, "bbox": {"x1": 34, "x2": 302, "y1": 248, "y2": 346}, "width": 268, "height": 98, "class_id": 1, "class_name": "scratch", "confidence": 0.4787, "area_percentage": 13.15, "confidence_percent": 47.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}, "detection_count": 2, "image_dimensions": {"width": 547, "height": 365}}	2684	1	t	\N	317e0d97-44e1-4f5d-9252-b662745d19b1	2026-08-18 12:45:07.274656+05:30	2026-08-18 12:45:07.274656+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	831c1497-13f3-4a93-818a-a1c50469cb97	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 18109, "bbox": {"x1": 251, "x2": 450, "y1": 337, "y2": 428}, "width": 199, "height": 91, "class_id": 1, "class_name": "scratch", "confidence": 0.3884, "area_percentage": 5.91, "confidence_percent": 38.8}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}, "detection_count": 1, "image_dimensions": {"width": 678, "height": 452}}	2682	1	t	\N	018b1bc4-43ee-4579-ae68-92237ad15ea6	2026-08-18 12:45:10.508067+05:30	2026-08-18 12:45:10.508067+05:30
ba268fb6-dcf4-43c5-b75d-495f02f02e24	b3e19897-20fc-4adf-8ee2-3ce0b2fd9986	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 30856, "bbox": {"x1": 125, "x2": 328, "y1": 99, "y2": 251}, "width": 203, "height": 152, "class_id": 1, "class_name": "scratch", "confidence": 0.6395, "area_percentage": 24.92, "confidence_percent": 63.9}, {"area": 22491, "bbox": {"x1": 144, "x2": 333, "y1": 4, "y2": 123}, "width": 189, "height": 119, "class_id": 1, "class_name": "scratch", "confidence": 0.517, "area_percentage": 18.16, "confidence_percent": 51.7}, {"area": 34944, "bbox": {"x1": 11, "x2": 235, "y1": 90, "y2": 246}, "width": 224, "height": 156, "class_id": 1, "class_name": "scratch", "confidence": 0.3909, "area_percentage": 28.22, "confidence_percent": 39.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 1910.42, "brightness": 97.42}, "detection_count": 3, "image_dimensions": {"width": 343, "height": 361}}	5569	1	t	\N	eaefbfc2-3d5b-4b17-825d-762e638a79a7	2026-08-18 13:05:39.46747+05:30	2026-08-18 13:05:39.46747+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	d0a2e6f1-e881-49c1-afc4-aea5eb300b14	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 38772, "bbox": {"x1": 268, "x2": 627, "y1": 73, "y2": 181}, "width": 359, "height": 108, "class_id": 1, "class_name": "scratch", "confidence": 0.6048, "above_threshold": true, "area_percentage": 18.68, "confidence_percent": 60.5}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}, "detection_count": 1, "image_dimensions": {"width": 674, "height": 308}}	4764	1	t	\N	41b41092-e547-4512-9a03-b46913cc983e	2026-08-18 13:25:49.071335+05:30	2026-08-18 13:25:49.071335+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	13e9d380-3ce5-48ef-a0af-17d28878f3d3	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 249500, "bbox": {"x1": 22, "x2": 522, "y1": 1, "y2": 500}, "width": 500, "height": 499, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5898, "above_threshold": true, "area_percentage": 50.13, "confidence_percent": 59.0}, {"area": 231080, "bbox": {"x1": 438, "x2": 862, "y1": 12, "y2": 557}, "width": 424, "height": 545, "class_id": 3, "class_name": "glass shatter", "confidence": 0.5078, "above_threshold": true, "area_percentage": 46.43, "confidence_percent": 50.8}, {"area": 65968, "bbox": {"x1": 596, "x2": 862, "y1": 326, "y2": 574}, "width": 266, "height": 248, "class_id": 1, "class_name": "scratch", "confidence": 0.3061, "above_threshold": false, "area_percentage": 13.26, "confidence_percent": 30.6}, {"area": 63840, "bbox": {"x1": 596, "x2": 862, "y1": 335, "y2": 575}, "width": 266, "height": 240, "class_id": 0, "class_name": "dent", "confidence": 0.2914, "above_threshold": false, "area_percentage": 12.83, "confidence_percent": 29.1}, {"area": 133424, "bbox": {"x1": 243, "x2": 512, "y1": 74, "y2": 570}, "width": 269, "height": 496, "class_id": 0, "class_name": "dent", "confidence": 0.2629, "above_threshold": false, "area_percentage": 26.81, "confidence_percent": 26.3}, {"area": 10738, "bbox": {"x1": 253, "x2": 344, "y1": 199, "y2": 317}, "width": 91, "height": 118, "class_id": 0, "class_name": "dent", "confidence": 0.1985, "above_threshold": false, "area_percentage": 2.16, "confidence_percent": 19.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}, "detection_count": 6, "image_dimensions": {"width": 864, "height": 576}}	2678	1	t	\N	3a943071-c7b3-4b58-becc-b6cdd99df47c	2026-08-18 13:25:51.891093+05:30	2026-08-18 13:25:51.891093+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dadaa205-d762-4b55-883f-dce322cb3299	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 91476, "bbox": {"x1": 267, "x2": 729, "y1": 124, "y2": 322}, "width": 462, "height": 198, "class_id": 1, "class_name": "scratch", "confidence": 0.3066, "above_threshold": true, "area_percentage": 29.84, "confidence_percent": 30.7}, {"area": 84597, "bbox": {"x1": 4, "x2": 493, "y1": 122, "y2": 295}, "width": 489, "height": 173, "class_id": 1, "class_name": "scratch", "confidence": 0.2137, "above_threshold": false, "area_percentage": 27.6, "confidence_percent": 21.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	1772	1	t	\N	1924d760-dbd0-4042-a826-1c42b17a3af7	2026-08-18 13:29:10.939241+05:30	2026-08-18 13:29:10.939241+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": true, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": true, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2240	1	t	\N	63a5cf8b-7fc9-44cc-a554-ff8453961df2	2026-08-18 13:29:13.86748+05:30	2026-08-18 13:29:13.86748+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	209d7f94-3f02-4cbe-9179-f08b8f32821c	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 648, "bbox": {"x1": 285, "x2": 303, "y1": 81, "y2": 117}, "width": 18, "height": 36, "class_id": 2, "class_name": "crack", "confidence": 0.6132, "above_threshold": true, "area_percentage": 0.32, "confidence_percent": 61.3}, {"area": 26264, "bbox": {"x1": 34, "x2": 302, "y1": 248, "y2": 346}, "width": 268, "height": 98, "class_id": 1, "class_name": "scratch", "confidence": 0.4787, "above_threshold": true, "area_percentage": 13.15, "confidence_percent": 47.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}, "detection_count": 2, "image_dimensions": {"width": 547, "height": 365}}	2256	1	t	\N	2b0bb07b-1516-44f2-963a-4c91e642b7bb	2026-08-18 13:29:16.757001+05:30	2026-08-18 13:29:16.757001+05:30
074094a4-77af-408c-ab06-6eda073d3df8	b6b8ee05-8838-4f76-a97c-655f47d0d151	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": true, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": true, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2589	1	t	\N	54da6101-36ac-4421-8a50-9487ad5e388d	2026-08-18 13:31:33.939248+05:30	2026-08-18 13:31:33.939248+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	55019291-31ab-4d88-be1a-a97d94698b36	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": false, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": false, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.5, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2555	1	t	\N	c148406c-abf7-45b7-960c-3258e850118f	2026-08-18 13:32:28.56966+05:30	2026-08-18 13:32:28.56966+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	56b9c8b4-bda2-4763-b70f-58cf376cbd75	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 18109, "bbox": {"x1": 251, "x2": 450, "y1": 337, "y2": 428}, "width": 199, "height": 91, "class_id": 1, "class_name": "scratch", "confidence": 0.3884, "above_threshold": false, "area_percentage": 5.91, "confidence_percent": 38.8}, {"area": 4074, "bbox": {"x1": 148, "x2": 245, "y1": 409, "y2": 451}, "width": 97, "height": 42, "class_id": 1, "class_name": "scratch", "confidence": 0.3037, "above_threshold": false, "area_percentage": 1.33, "confidence_percent": 30.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.5, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}, "detection_count": 2, "image_dimensions": {"width": 678, "height": 452}}	2693	1	t	\N	ce4c9e98-2bbd-4d7e-aae9-79954f9fe5ca	2026-08-18 13:32:35.847041+05:30	2026-08-18 13:32:35.847041+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	32152275-4ba8-4a3d-9f54-9abd4c09a271	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 18109, "bbox": {"x1": 251, "x2": 450, "y1": 337, "y2": 428}, "width": 199, "height": 91, "class_id": 1, "class_name": "scratch", "confidence": 0.3884, "above_threshold": true, "area_percentage": 5.91, "confidence_percent": 38.8}, {"area": 4074, "bbox": {"x1": 148, "x2": 245, "y1": 409, "y2": 451}, "width": 97, "height": 42, "class_id": 1, "class_name": "scratch", "confidence": 0.3037, "above_threshold": true, "area_percentage": 1.33, "confidence_percent": 30.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}, "detection_count": 2, "image_dimensions": {"width": 678, "height": 452}}	2280	1	t	\N	fbda9881-4892-4f41-ad80-ad7c5264562d	2026-08-18 13:29:19.701734+05:30	2026-08-18 13:29:19.701734+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	47001255-28ba-43c1-aebf-072b6817411a	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 91476, "bbox": {"x1": 267, "x2": 729, "y1": 124, "y2": 322}, "width": 462, "height": 198, "class_id": 1, "class_name": "scratch", "confidence": 0.3066, "above_threshold": false, "area_percentage": 29.84, "confidence_percent": 30.7}, {"area": 84597, "bbox": {"x1": 4, "x2": 493, "y1": 122, "y2": 295}, "width": 489, "height": 173, "class_id": 1, "class_name": "scratch", "confidence": 0.2137, "above_threshold": false, "area_percentage": 27.6, "confidence_percent": 21.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.5, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	2005	1	t	\N	b8f0eb52-6cc4-4e0c-b4ae-24fe5b6b165e	2026-08-18 13:32:25.250256+05:30	2026-08-18 13:32:25.250256+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	610f294b-4b90-499a-8b32-93ddabe4ed6b	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 648, "bbox": {"x1": 285, "x2": 303, "y1": 81, "y2": 117}, "width": 18, "height": 36, "class_id": 2, "class_name": "crack", "confidence": 0.6132, "above_threshold": true, "area_percentage": 0.32, "confidence_percent": 61.3}, {"area": 26264, "bbox": {"x1": 34, "x2": 302, "y1": 248, "y2": 346}, "width": 268, "height": 98, "class_id": 1, "class_name": "scratch", "confidence": 0.4787, "above_threshold": false, "area_percentage": 13.15, "confidence_percent": 47.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.5, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}, "detection_count": 2, "image_dimensions": {"width": 547, "height": 365}}	3258	1	t	\N	985c6fe9-ac53-4f03-a406-5b1342a00c58	2026-08-18 13:32:32.455462+05:30	2026-08-18 13:32:32.455462+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	37bb03ec-5aa6-4fdd-8a9b-68d21fa4f1a8	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 91476, "bbox": {"x1": 267, "x2": 729, "y1": 124, "y2": 322}, "width": 462, "height": 198, "class_id": 1, "class_name": "scratch", "confidence": 0.3066, "above_threshold": false, "area_percentage": 29.84, "confidence_percent": 30.7}, {"area": 84597, "bbox": {"x1": 4, "x2": 493, "y1": 122, "y2": 295}, "width": 489, "height": 173, "class_id": 1, "class_name": "scratch", "confidence": 0.2137, "above_threshold": false, "area_percentage": 27.6, "confidence_percent": 21.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	7622	1	t	\N	37080ae1-7cf7-44c9-bdd3-4e6046731477	2026-08-18 16:22:49.826107+05:30	2026-08-18 16:22:49.826107+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	a3e066b5-8aba-4e2d-be33-485ca76e361f	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": true, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": false, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2891	1	t	\N	13709d48-cd55-49bb-95a9-03a0d13ec8fc	2026-08-18 16:22:53.557986+05:30	2026-08-18 16:22:53.557986+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	d41fc5b7-4b31-4220-91a8-abd94c433865	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 648, "bbox": {"x1": 285, "x2": 303, "y1": 81, "y2": 117}, "width": 18, "height": 36, "class_id": 2, "class_name": "crack", "confidence": 0.6132, "above_threshold": true, "area_percentage": 0.32, "confidence_percent": 61.3}, {"area": 26264, "bbox": {"x1": 34, "x2": 302, "y1": 248, "y2": 346}, "width": 268, "height": 98, "class_id": 1, "class_name": "scratch", "confidence": 0.4787, "above_threshold": true, "area_percentage": 13.15, "confidence_percent": 47.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}, "detection_count": 2, "image_dimensions": {"width": 547, "height": 365}}	2809	1	t	\N	9b0b2d2f-a0be-4883-a6ed-3cb00f85f08b	2026-08-18 16:22:57.972872+05:30	2026-08-18 16:22:57.972872+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	4974153c-05e9-4171-84f2-6f950b163d22	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 18109, "bbox": {"x1": 251, "x2": 450, "y1": 337, "y2": 428}, "width": 199, "height": 91, "class_id": 1, "class_name": "scratch", "confidence": 0.3884, "above_threshold": true, "area_percentage": 5.91, "confidence_percent": 38.8}, {"area": 4074, "bbox": {"x1": 148, "x2": 245, "y1": 409, "y2": 451}, "width": 97, "height": 42, "class_id": 1, "class_name": "scratch", "confidence": 0.3037, "above_threshold": false, "area_percentage": 1.33, "confidence_percent": 30.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}, "detection_count": 2, "image_dimensions": {"width": 678, "height": 452}}	2768	1	t	\N	22b98a00-e49c-4baa-88d9-73a96d5ab7bd	2026-08-18 16:23:01.421816+05:30	2026-08-18 16:23:01.421816+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	0020b111-0adb-4e04-a807-b4fbe7226233	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 91476, "bbox": {"x1": 267, "x2": 729, "y1": 124, "y2": 322}, "width": 462, "height": 198, "class_id": 1, "class_name": "scratch", "confidence": 0.3066, "above_threshold": true, "area_percentage": 29.84, "confidence_percent": 30.7}, {"area": 84597, "bbox": {"x1": 4, "x2": 493, "y1": 122, "y2": 295}, "width": 489, "height": 173, "class_id": 1, "class_name": "scratch", "confidence": 0.2137, "above_threshold": false, "area_percentage": 27.6, "confidence_percent": 21.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	2238	1	t	\N	e0650da2-5977-476f-b028-47ffc8f85a13	2026-08-18 16:27:44.361517+05:30	2026-08-18 16:27:44.361517+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	db644740-6b72-4998-adaa-52d04816f7f2	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": true, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": true, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2815	1	t	\N	74187521-80e5-4cbe-96de-3213fb62e523	2026-08-18 16:27:47.811148+05:30	2026-08-18 16:27:47.811148+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 255640, "bbox": {"x1": 0, "x2": 616, "y1": 152, "y2": 567}, "width": 616, "height": 415, "class_id": 0, "class_name": "dent", "confidence": 0.8646, "above_threshold": true, "area_percentage": 24.38, "confidence_percent": 86.5}, {"area": 78705, "bbox": {"x1": 522, "x2": 819, "y1": 375, "y2": 640}, "width": 297, "height": 265, "class_id": 0, "class_name": "dent", "confidence": 0.7152, "above_threshold": true, "area_percentage": 7.51, "confidence_percent": 71.5}, {"area": 285, "bbox": {"x1": 184, "x2": 203, "y1": 808, "y2": 823}, "width": 19, "height": 15, "class_id": 0, "class_name": "dent", "confidence": 0.3973, "above_threshold": true, "area_percentage": 0.03, "confidence_percent": 39.7}, {"area": 700, "bbox": {"x1": 765, "x2": 793, "y1": 434, "y2": 459}, "width": 28, "height": 25, "class_id": 0, "class_name": "dent", "confidence": 0.2807, "above_threshold": true, "area_percentage": 0.07, "confidence_percent": 28.1}, {"area": 812, "bbox": {"x1": 240, "x2": 268, "y1": 797, "y2": 826}, "width": 28, "height": 29, "class_id": 0, "class_name": "dent", "confidence": 0.2681, "above_threshold": true, "area_percentage": 0.08, "confidence_percent": 26.8}, {"area": 1240, "bbox": {"x1": 61, "x2": 101, "y1": 786, "y2": 817}, "width": 40, "height": 31, "class_id": 0, "class_name": "dent", "confidence": 0.1906, "above_threshold": false, "area_percentage": 0.12, "confidence_percent": 19.1}, {"area": 483, "bbox": {"x1": 140, "x2": 161, "y1": 781, "y2": 804}, "width": 21, "height": 23, "class_id": 0, "class_name": "dent", "confidence": 0.1763, "above_threshold": false, "area_percentage": 0.05, "confidence_percent": 17.6}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.22, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 974.56, "brightness": 85.6}, "detection_count": 7, "image_dimensions": {"width": 1024, "height": 1024}}	8046	1	t	\N	234c9855-49c1-471b-9683-0181380f222f	2026-08-18 18:20:29.875764+05:30	2026-08-18 18:20:29.875764+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	f5a9d4ae-6401-4e57-8073-ab989174c63c	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 91476, "bbox": {"x1": 267, "x2": 729, "y1": 124, "y2": 322}, "width": 462, "height": 198, "class_id": 1, "class_name": "scratch", "confidence": 0.3066, "above_threshold": false, "area_percentage": 29.84, "confidence_percent": 30.7}, {"area": 84597, "bbox": {"x1": 4, "x2": 493, "y1": 122, "y2": 295}, "width": 489, "height": 173, "class_id": 1, "class_name": "scratch", "confidence": 0.2137, "above_threshold": false, "area_percentage": 27.6, "confidence_percent": 21.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}, "detection_count": 2, "image_dimensions": {"width": 782, "height": 392}}	2422	1	t	\N	bac30205-cc6f-4ef8-9cf3-b4378fa54850	2026-08-18 19:12:35.150871+05:30	2026-08-18 19:12:35.150871+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	75bb6f49-597f-4630-bfe1-6b436744a217	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 154845, "bbox": {"x1": 129, "x2": 684, "y1": 61, "y2": 340}, "width": 555, "height": 279, "class_id": 3, "class_name": "glass shatter", "confidence": 0.4722, "above_threshold": true, "area_percentage": 21.51, "confidence_percent": 47.2}, {"area": 203490, "bbox": {"x1": 3, "x2": 649, "y1": 320, "y2": 635}, "width": 646, "height": 315, "class_id": 1, "class_name": "scratch", "confidence": 0.2505, "above_threshold": false, "area_percentage": 28.27, "confidence_percent": 25.1}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}, "detection_count": 2, "image_dimensions": {"width": 1024, "height": 703}}	2719	1	t	\N	1de8fe6a-e636-4cf9-a545-ee54b513e8b2	2026-08-18 19:12:39.278719+05:30	2026-08-18 19:12:39.278719+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	049e1d42-6d2d-452f-9147-43ab3a616694	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 648, "bbox": {"x1": 285, "x2": 303, "y1": 81, "y2": 117}, "width": 18, "height": 36, "class_id": 2, "class_name": "crack", "confidence": 0.6132, "above_threshold": true, "area_percentage": 0.32, "confidence_percent": 61.3}, {"area": 26264, "bbox": {"x1": 34, "x2": 302, "y1": 248, "y2": 346}, "width": 268, "height": 98, "class_id": 1, "class_name": "scratch", "confidence": 0.4787, "above_threshold": true, "area_percentage": 13.15, "confidence_percent": 47.9}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}, "detection_count": 2, "image_dimensions": {"width": 547, "height": 365}}	2778	1	t	\N	47a55983-4fe7-41ac-9ba1-97bbe6702a3b	2026-08-18 19:12:43.052953+05:30	2026-08-18 19:12:43.052953+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	e08d1eb7-ba4d-4a0a-b173-3e4b0d4f7d2b	ultralytics	autodent-yolo11m	1.0.0	{"device": "cpu", "backend": "ultralytics", "detections": [{"area": 18109, "bbox": {"x1": 251, "x2": 450, "y1": 337, "y2": 428}, "width": 199, "height": 91, "class_id": 1, "class_name": "scratch", "confidence": 0.3884, "above_threshold": true, "area_percentage": 5.91, "confidence_percent": 38.8}, {"area": 4074, "bbox": {"x1": 148, "x2": 245, "y1": 409, "y2": 451}, "width": 97, "height": 42, "class_id": 1, "class_name": "scratch", "confidence": 0.3037, "above_threshold": false, "area_percentage": 1.33, "confidence_percent": 30.4}], "model_path": "models/best.pt", "parameters": {"iou": 0.45, "conf": 0.35, "clahe": false, "imgsz": 1024, "augment": false, "detection_floor": 0.15, "fallback_pass_used": false}, "class_names": {"0": "dent", "1": "scratch", "2": "crack", "3": "glass shatter", "4": "lamp broken", "5": "tire flat"}, "image_quality": {"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}, "detection_count": 2, "image_dimensions": {"width": 678, "height": 452}}	2655	1	t	\N	abab963a-438e-4183-9829-1a5fe7287ab1	2026-08-18 19:12:46.27938+05:30	2026-08-18 19:12:46.27938+05:30
\.


--
-- Data for Name: inspection_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inspection_images (inspection_id, cloudinary_public_id, secure_url, thumbnail_url, view_angle, width, height, file_size_bytes, format, sequence_no, status, failure_reason, quality_report, annotated_url, id, created_at, updated_at) FROM stdin;
64c0e21e-8228-4345-875d-5b3002a306cd	car	https://res.cloudinary.com/demo/image/upload/car.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/car.jpg	front	1920	1080	500000	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}	\N	d635b741-cbf2-42b5-b699-64dafae438bc	2026-08-18 11:59:10.739858+05:30	2026-08-18 11:59:21.353747+05:30
64c0e21e-8228-4345-875d-5b3002a306cd	sample	https://res.cloudinary.com/demo/image/upload/sample.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/sample.jpg	left	1920	1080	500000	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}	\N	ba5683f6-af06-498d-9e7b-7a7fda54c12b	2026-08-18 11:59:10.739858+05:30	2026-08-18 11:59:25.454424+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	car	https://res.cloudinary.com/demo/image/upload/car.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/car.jpg	front	1920	1080	500000	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}	\N	058d673a-1b82-42c7-b9b0-f54eddc4369f	2026-08-18 12:02:19.436253+05:30	2026-08-18 12:02:26.401379+05:30
f11c86cf-10e4-4976-9770-354a48ee4188	sample	https://res.cloudinary.com/demo/image/upload/sample.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/sample.jpg	left	1920	1080	500000	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}	\N	137be88f-3711-4ad5-b8fc-f21d557ee651	2026-08-18 12:02:19.436253+05:30	2026-08-18 12:02:30.615105+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	car	https://res.cloudinary.com/demo/image/upload/car.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/car.jpg	front	1920	1080	500000	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}	\N	cba4a5b6-f197-4569-93da-77bea6f4d53a	2026-08-18 12:04:46.289029+05:30	2026-08-18 12:04:55.94658+05:30
fdcc89e3-ee04-42b2-975b-c67898226fe8	sample	https://res.cloudinary.com/demo/image/upload/sample.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/sample.jpg	left	1920	1080	500000	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}	\N	61c08572-1825-4c3c-9d1e-28fc6d0c7892	2026-08-18 12:04:46.289029+05:30	2026-08-18 12:04:59.278405+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96	https://res.cloudinary.com/utlka8ks/image/upload/v1787037277/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037277/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	b3c1425e-776f-40a7-81bc-ed57a2e56734	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:44:59.964679+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf	https://res.cloudinary.com/utlka8ks/image/upload/v1787037278/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037278/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	76aae949-89b9-4565-a491-c9ec44fb0923	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:03.833966+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug	https://res.cloudinary.com/utlka8ks/image/upload/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	\N	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:07.277655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf	https://res.cloudinary.com/utlka8ks/image/upload/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	\N	831c1497-13f3-4a93-818a-a1c50469cb97	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:10.509828+05:30
ba268fb6-dcf4-43c5-b75d-495f02f02e24	dent-inspections/50cae379-0ad7-47bd-8420-27a5200c4119/lz4efr1ojqdw2hpsnxqv	https://res.cloudinary.com/utlka8ks/image/upload/v1787038532/dent-inspections/50cae379-0ad7-47bd-8420-27a5200c4119/lz4efr1ojqdw2hpsnxqv.png	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787038532/dent-inspections/50cae379-0ad7-47bd-8420-27a5200c4119/lz4efr1ojqdw2hpsnxqv.png	\N	343	361	13057	png	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 1910.42, "brightness": 97.42}	\N	b3e19897-20fc-4adf-8ee2-3ce0b2fd9986	2026-08-18 13:05:33.236769+05:30	2026-08-18 13:05:39.47047+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	car	https://res.cloudinary.com/demo/image/upload/car.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/car.jpg	front	1920	1080	500000	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 759.98, "brightness": 170.39}	\N	d0a2e6f1-e881-49c1-afc4-aea5eb300b14	2026-08-18 13:25:44.022441+05:30	2026-08-18 13:25:49.087851+05:30
1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	sample	https://res.cloudinary.com/demo/image/upload/sample.jpg	https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/sample.jpg	left	1920	1080	500000	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 106.32, "brightness": 111.52}	\N	13e9d380-3ce5-48ef-a0af-17d28878f3d3	2026-08-18 13:25:44.022441+05:30	2026-08-18 13:25:51.895092+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k	https://res.cloudinary.com/utlka8ks/image/upload/v1787039945/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039945/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	dadaa205-d762-4b55-883f-dce322cb3299	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:10.94124+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid	https://res.cloudinary.com/utlka8ks/image/upload/v1787039946/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039946/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:13.868479+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec	https://res.cloudinary.com/utlka8ks/image/upload/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	\N	209d7f94-3f02-4cbe-9179-f08b8f32821c	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:16.759006+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm	https://res.cloudinary.com/utlka8ks/image/upload/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	\N	32152275-4ba8-4a3d-9f54-9abd4c09a271	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:19.702735+05:30
074094a4-77af-408c-ab06-6eda073d3df8	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf	https://res.cloudinary.com/utlka8ks/image/upload/v1787040090/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040090/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf.jpg	\N	1300	893	189916	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	b6b8ee05-8838-4f76-a97c-655f47d0d151	2026-08-18 13:31:30.587732+05:30	2026-08-18 13:31:33.940245+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv	https://res.cloudinary.com/utlka8ks/image/upload/v1787040140/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040140/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	47001255-28ba-43c1-aebf-072b6817411a	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:25.251256+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q	https://res.cloudinary.com/utlka8ks/image/upload/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	55019291-31ab-4d88-be1a-a97d94698b36	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:28.564658+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca	https://res.cloudinary.com/utlka8ks/image/upload/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	\N	610f294b-4b90-499a-8b32-93ddabe4ed6b	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:32.456464+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7	https://res.cloudinary.com/utlka8ks/image/upload/v1787040142/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040142/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	\N	56b9c8b4-bda2-4763-b70f-58cf376cbd75	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:35.841038+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy	https://res.cloudinary.com/utlka8ks/image/upload/v1787050357/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050357/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	37bb03ec-5aa6-4fdd-8a9b-68d21fa4f1a8	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:49.844106+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg	https://res.cloudinary.com/utlka8ks/image/upload/v1787050359/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050359/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	a3e066b5-8aba-4e2d-be33-485ca76e361f	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:53.559987+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl	https://res.cloudinary.com/utlka8ks/image/upload/v1787050360/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050360/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	\N	d41fc5b7-4b31-4220-91a8-abd94c433865	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:57.974871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj	https://res.cloudinary.com/utlka8ks/image/upload/v1787050361/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050361/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	\N	4974153c-05e9-4171-84f2-6f950b163d22	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:23:01.423813+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79	https://res.cloudinary.com/utlka8ks/image/upload/v1787050659/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050659/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	0020b111-0adb-4e04-a807-b4fbe7226233	2026-08-18 16:27:41.416937+05:30	2026-08-18 16:27:44.363519+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv	https://res.cloudinary.com/utlka8ks/image/upload/v1787050661/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050661/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	db644740-6b72-4998-adaa-52d04816f7f2	2026-08-18 16:27:41.416937+05:30	2026-08-18 16:27:47.823149+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq	https://res.cloudinary.com/utlka8ks/image/upload/v1787057420/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787057420/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq.jpg	\N	1024	1024	128400	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 974.56, "brightness": 85.6}	\N	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	2026-08-18 18:20:20.483339+05:30	2026-08-18 18:20:29.879764+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc	https://res.cloudinary.com/utlka8ks/image/upload/v1787060549/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060549/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	\N	f5a9d4ae-6401-4e57-8073-ab989174c63c	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:35.153871+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm	https://res.cloudinary.com/utlka8ks/image/upload/v1787060550/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060550/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	\N	75bb6f49-597f-4630-bfe1-6b436744a217	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:39.281717+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor	https://res.cloudinary.com/utlka8ks/image/upload/v1787060551/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060551/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	\N	049e1d42-6d2d-452f-9147-43ab3a616694	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:43.055949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf	https://res.cloudinary.com/utlka8ks/image/upload/v1787060552/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060552/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	\N	e08d1eb7-ba4d-4a0a-b173-3e4b0d4f7d2b	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:46.281382+05:30
\.


--
-- Data for Name: inspections; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inspections (user_id, vehicle_id, reference_code, status, overall_severity, damage_score, total_detections, image_count, total_area_percent, damage_summary, model_name, model_version, processing_started_at, processing_completed_at, processing_ms, error_code, error_message, idempotency_key, id, created_at, updated_at, deleted_at, detection_preset, detection_settings, below_threshold_count) FROM stdin;
9045966b-808f-4288-a3f9-b71e4fa728a4	dedebf9a-474d-4e0d-9d53-0e2bce57269e	INS-20260818-6EA852	completed	severe	100	3	2	57.62	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 18.68}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 96.57}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 12:04:46.442577+05:30	2026-08-18 12:04:59.31348+05:30	12871	\N	\N	smoke-cc6e308b	fdcc89e3-ee04-42b2-975b-c67898226fe8	2026-08-18 12:04:46.285031+05:30	2026-08-18 12:05:02.409819+05:30	2026-08-18 12:05:02.40882+05:30	\N	\N	0
f447b79b-44ec-4453-8ec4-ec15486c6aa6	abe112d1-f120-4917-b68b-93dea76f791a	INS-20260818-11372A	completed	severe	100	3	2	115.24	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 18.68}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 96.57}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 12:02:19.45625+05:30	2026-08-18 12:02:30.638105+05:30	11181	\N	\N	smoke-2e2a0241	f11c86cf-10e4-4976-9770-354a48ee4188	2026-08-18 12:02:19.43425+05:30	2026-08-18 12:02:32.254188+05:30	2026-08-18 12:02:32.253187+05:30	\N	\N	0
0ead12f2-9078-4321-9aac-6bb780cd43c8	810b2960-2dbb-4a21-84a8-dfb17725a1e8	INS-20260818-226A4A	completed	severe	100	3	2	57.62	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 18.68}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 96.57}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 12:07:51.003197+05:30	2026-08-18 12:08:03.799179+05:30	12795	\N	\N	smoke-run-001	64c0e21e-8228-4345-875d-5b3002a306cd	2026-08-18 11:59:10.734858+05:30	2026-08-18 12:08:03.800179+05:30	\N	\N	\N	0
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-E00A8E	completed	severe	100	5	4	22.27	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 3, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 67.23}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 12:44:40.085598+05:30	2026-08-18 12:45:10.536881+05:30	30451	\N	\N	ui-74c4bfb4-bf35-436d-b333-cfbe8046f257	b9ddc102-aa6c-40bb-9cca-71dab429b2ab	2026-08-18 12:44:40.029596+05:30	2026-08-18 12:45:10.53788+05:30	\N	\N	\N	0
50cae379-0ad7-47bd-8420-27a5200c4119	5b67c405-8de6-4b50-996c-5450c9f289c4	INS-20260818-0A3C85	completed	severe	64	3	1	71.3	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 3, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 71.3}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:05:33.254303+05:30	2026-08-18 13:05:39.492982+05:30	6239	\N	\N	ui-1787038531	ba268fb6-dcf4-43c5-b75d-495f02f02e24	2026-08-18 13:05:33.234769+05:30	2026-08-18 13:05:39.493983+05:30	\N	\N	\N	0
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-3F1E1F	completed	severe	100	7	4	25.08	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 5, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 78.5}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:29:08.063431+05:30	2026-08-18 13:29:19.725737+05:30	11662	\N	\N	ui-4d4802ba-e586-435c-88e6-101d0a8a9031	cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	2026-08-18 13:29:08.040434+05:30	2026-08-18 13:29:19.726739+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	1
36be2a51-656f-4dac-9719-7fa19af75dc4	b441dfca-4f35-47e4-981e-40cce64d1e74	INS-20260818-5770E0	completed	severe	100	3	2	57.62	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 18.68}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 96.57}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:25:44.160951+05:30	2026-08-18 13:25:51.931092+05:30	7770	\N	\N	smoke-513cc8b7	1199c22a-9ed9-4deb-8bd9-d8a85e90ab6b	2026-08-18 13:25:44.006437+05:30	2026-08-18 13:25:53.703885+05:30	2026-08-18 13:25:53.702886+05:30	balanced	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.35, "input_size": 1024}	4
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-B48066	completed	severe	81	2	1	49.78	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 28.27}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:31:30.618323+05:30	2026-08-18 13:31:33.959246+05:30	3341	\N	\N	ui-9c542ef4-3011-4de1-b644-0561937237d9	074094a4-77af-408c-ab06-6eda073d3df8	2026-08-18 13:31:30.584735+05:30	2026-08-18 13:31:33.960247+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	0
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-23E9EA	completed	minor	8	1	4	0.08	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 0, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:32:22.622228+05:30	2026-08-18 13:32:35.868041+05:30	13245	\N	\N	ui-07e6f93b-cc63-43bb-80f0-01384246949f	cd669392-b28f-4dd0-a260-6a10d074c28b	2026-08-18 13:32:22.600791+05:30	2026-08-18 13:32:35.869041+05:30	\N	strict	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.5, "input_size": 1024}	7
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-4FBDDE	completed	severe	97	4	4	10.22	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 19.06}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 16:22:41.371264+05:30	2026-08-18 16:23:01.451816+05:30	20080	\N	\N	ui-1d72d076-0566-4124-a0fc-130a36eaab6d	514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	2026-08-18 16:22:41.293252+05:30	2026-08-18 16:23:01.452814+05:30	\N	balanced	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.35, "input_size": 1024}	4
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-653687	completed	severe	89	3	2	39.81	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 58.11}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 16:27:41.441937+05:30	2026-08-18 16:27:47.845699+05:30	6403	\N	\N	ui-26019eb6-e9aa-4044-bee2-1e9d32a7696b	7a36f7ea-a229-4f10-9005-49673489c5f5	2026-08-18 16:27:41.414939+05:30	2026-08-18 16:27:47.846699+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	1
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-B08575	completed	severe	80	5	1	32.06	[{"count": 5, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": "severe", "total_area_percent": 32.06}, {"count": 0, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 18:20:20.529012+05:30	2026-08-18 18:20:29.912804+05:30	9383	\N	\N	ui-ec67e7a3-6dc3-4428-979a-45d8089dc547	08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	2026-08-18 18:20:20.477337+05:30	2026-08-18 18:20:29.913853+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	2
1159bb7c-34c8-44b1-a542-9aa1c7512f55	\N	INS-20260818-4E58B2	completed	severe	97	4	4	10.22	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 19.06}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 19:12:32.191329+05:30	2026-08-18 19:12:46.308379+05:30	14117	\N	\N	ui-4095e1b5-d43c-4155-8363-5a019e8462bf	8cb902b4-f113-4d88-a3d1-28646407bcb7	2026-08-18 19:12:32.148327+05:30	2026-08-18 19:12:46.309379+05:30	\N	balanced	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.35, "input_size": 1024}	4
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (email, password_hash, full_name, phone, role, is_active, id, created_at, updated_at, deleted_at) FROM stdin;
smoke@example.com	scrypt:32768:8:1$Wc7pKpRmW49hLFo2$7fc3da662ea6c6c2d12d001969c2c9b51b4250b62f698560747aec8374100d0e6d45ad9d99218025817cb531c2b18c8ae3c424a1e3210461e459ad4bfa871a2f	Smoke Test	\N	user	t	0ead12f2-9078-4321-9aac-6bb780cd43c8	2026-08-18 11:59:10.180415+05:30	2026-08-18 11:59:10.180415+05:30	\N
smoke-2e2a0241@example.com	scrypt:32768:8:1$ZYBP5p24qhbGzndl$4073e8325a347c0e75fa714d533386112559774f38dbe8e8f7e6bbc8c0e189a24656f1428fe0d64a3afd66e42d9084ae0a9cb069d272446f8322e93565855b6f	Smoke Test	\N	user	t	f447b79b-44ec-4453-8ec4-ec15486c6aa6	2026-08-18 12:02:18.853413+05:30	2026-08-18 12:02:18.853413+05:30	\N
intruder-2e2a0241@example.com	scrypt:32768:8:1$kJLirrZij0BtpBqe$f209e916572566d048a15abd1b43f28794c41259065c483d26ad69ea4e87bd5320756d95107c9664dc93d53b18ee16f6d55016a8ba8cdf1f011e32e3d688a0f9	\N	\N	user	t	1488c4fe-4675-4b31-96c4-d54bb582387d	2026-08-18 12:02:32.150634+05:30	2026-08-18 12:02:32.150634+05:30	\N
smoke-cc6e308b@example.com	scrypt:32768:8:1$LecPrVEtIZGsDzbs$37034c80309bb08bf95ec1aa7d30d1d21396f3f106746f765299645886b7929bab8e4a77447ca6e2260549acfb2451d150722000e5aeb810499af79f70197623	Smoke Test	\N	user	t	9045966b-808f-4288-a3f9-b71e4fa728a4	2026-08-18 12:04:45.693819+05:30	2026-08-18 12:04:45.693819+05:30	\N
intruder-cc6e308b@example.com	scrypt:32768:8:1$SytP25h5KgNhkdCH$ccd4b7dc0b506c430a6aff9f3c2f4aec566988e28c6f1a043e7c094fcb4ae27e6ebfdff38b8b35ea886e6467f59397845fb9893ac84b0b704cc3402de0c8baed	\N	\N	user	t	f82f1560-0ebf-4a77-8f74-ab6205be5ac4	2026-08-18 12:05:02.313487+05:30	2026-08-18 12:05:02.313487+05:30	\N
test@yopmail.com	scrypt:32768:8:1$lmFAyTGklbhrHsq0$f4f8f7ae67f305df287ebeaa8cfa9c2b7fa00c4337846633349c39db88dbb2bcb8f09c2b87c86dfe639348482ca91e8e333d75bfc801be179968689352ae7b5d	Test	\N	user	t	1159bb7c-34c8-44b1-a542-9aa1c7512f55	2026-08-18 12:41:59.924247+05:30	2026-08-18 12:41:59.924247+05:30	\N
ui-1787038531@example.com	scrypt:32768:8:1$vhKfF2pdUcCuFSY3$fb506bc0692d5a0691f49ea5a92a5875caa8ffaacf28b2c8bb5e6bfea584be086e1ae93dfa6319ab9dbe61d36bca0c999b8f130e6759c042e309c7b548322a9d	UI Flow	\N	user	t	50cae379-0ad7-47bd-8420-27a5200c4119	2026-08-18 13:05:31.505047+05:30	2026-08-18 13:05:31.505047+05:30	\N
smoke-513cc8b7@example.com	scrypt:32768:8:1$3MSjTQpHAaRf1fcT$a55778d8f313243a24e2975952bc194cf4c31caec75ac570c9b392700874904ecda2c5048bc9e7436945bf1fca14ff9c8c86351305fb7be4797133ac8a4dac73	Smoke Test	\N	user	t	36be2a51-656f-4dac-9719-7fa19af75dc4	2026-08-18 13:25:43.546482+05:30	2026-08-18 13:25:43.547482+05:30	\N
intruder-513cc8b7@example.com	scrypt:32768:8:1$SGODtXi96dUCeEiU$abfb159091d35a352015581dc7e2e5da5cf2dba07a0d6dc7b743d2e4e5b87301496e0389ab20a906028ee511d853ced787d0f11fa19c7a213d7076ba95efa8f0	\N	\N	user	t	2a2a55c7-53d4-481b-8251-7ba9ebc51319	2026-08-18 13:25:53.621844+05:30	2026-08-18 13:25:53.621844+05:30	\N
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vehicles (user_id, registration_number, make, model, year, colour, id, created_at, updated_at) FROM stdin;
0ead12f2-9078-4321-9aac-6bb780cd43c8	MH12AB1234	Hyundai	Creta	2022	\N	810b2960-2dbb-4a21-84a8-dfb17725a1e8	2026-08-18 11:59:10.725861+05:30	2026-08-18 11:59:10.725861+05:30
f447b79b-44ec-4453-8ec4-ec15486c6aa6	MH12AB2E2A	Hyundai	Creta	2022	\N	abe112d1-f120-4917-b68b-93dea76f791a	2026-08-18 12:02:19.432249+05:30	2026-08-18 12:02:19.432249+05:30
9045966b-808f-4288-a3f9-b71e4fa728a4	MH12ABCC6E	Hyundai	Creta	2022	\N	dedebf9a-474d-4e0d-9d53-0e2bce57269e	2026-08-18 12:04:46.280023+05:30	2026-08-18 12:04:46.280023+05:30
50cae379-0ad7-47bd-8420-27a5200c4119	UI038531	Test	Vehicle	\N	\N	5b67c405-8de6-4b50-996c-5450c9f289c4	2026-08-18 13:05:33.233768+05:30	2026-08-18 13:05:33.233768+05:30
36be2a51-656f-4dac-9719-7fa19af75dc4	MH12AB513C	Hyundai	Creta	2022	\N	b441dfca-4f35-47e4-981e-40cce64d1e74	2026-08-18 13:25:44.002442+05:30	2026-08-18 13:25:44.002442+05:30
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: damage_types damage_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.damage_types
    ADD CONSTRAINT damage_types_pkey PRIMARY KEY (id);


--
-- Name: detections detections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_pkey PRIMARY KEY (id);


--
-- Name: inference_runs inference_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_runs
    ADD CONSTRAINT inference_runs_pkey PRIMARY KEY (id);


--
-- Name: inspection_images inspection_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspection_images
    ADD CONSTRAINT inspection_images_pkey PRIMARY KEY (id);


--
-- Name: inspections inspections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspections
    ADD CONSTRAINT inspections_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: ix_damage_types_class_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_damage_types_class_key ON public.damage_types USING btree (class_key);


--
-- Name: ix_detections_damage_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_damage_type_id ON public.detections USING btree (damage_type_id);


--
-- Name: ix_detections_inspection_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_inspection_id ON public.detections USING btree (inspection_id);


--
-- Name: ix_detections_inspection_image_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_inspection_image_id ON public.detections USING btree (inspection_image_id);


--
-- Name: ix_inference_runs_inspection_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inference_runs_inspection_id ON public.inference_runs USING btree (inspection_id);


--
-- Name: ix_inference_runs_inspection_image_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inference_runs_inspection_image_id ON public.inference_runs USING btree (inspection_image_id);


--
-- Name: ix_inspection_images_inspection_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspection_images_inspection_id ON public.inspection_images USING btree (inspection_id);


--
-- Name: ix_inspections_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_deleted_at ON public.inspections USING btree (deleted_at);


--
-- Name: ix_inspections_idempotency_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_inspections_idempotency_key ON public.inspections USING btree (idempotency_key);


--
-- Name: ix_inspections_reference_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_inspections_reference_code ON public.inspections USING btree (reference_code);


--
-- Name: ix_inspections_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_status ON public.inspections USING btree (status);


--
-- Name: ix_inspections_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_user_created ON public.inspections USING btree (user_id, created_at);


--
-- Name: ix_inspections_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_user_id ON public.inspections USING btree (user_id);


--
-- Name: ix_inspections_vehicle_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_vehicle_id ON public.inspections USING btree (vehicle_id);


--
-- Name: ix_users_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_deleted_at ON public.users USING btree (deleted_at);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_vehicles_registration_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vehicles_registration_number ON public.vehicles USING btree (registration_number);


--
-- Name: ix_vehicles_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vehicles_user_id ON public.vehicles USING btree (user_id);


--
-- Name: detections detections_damage_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_damage_type_id_fkey FOREIGN KEY (damage_type_id) REFERENCES public.damage_types(id) ON DELETE RESTRICT;


--
-- Name: detections detections_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspections(id) ON DELETE CASCADE;


--
-- Name: detections detections_inspection_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_inspection_image_id_fkey FOREIGN KEY (inspection_image_id) REFERENCES public.inspection_images(id) ON DELETE CASCADE;


--
-- Name: inference_runs inference_runs_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_runs
    ADD CONSTRAINT inference_runs_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspections(id) ON DELETE CASCADE;


--
-- Name: inference_runs inference_runs_inspection_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inference_runs
    ADD CONSTRAINT inference_runs_inspection_image_id_fkey FOREIGN KEY (inspection_image_id) REFERENCES public.inspection_images(id) ON DELETE CASCADE;


--
-- Name: inspection_images inspection_images_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspection_images
    ADD CONSTRAINT inspection_images_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspections(id) ON DELETE CASCADE;


--
-- Name: inspections inspections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspections
    ADD CONSTRAINT inspections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: inspections inspections_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspections
    ADD CONSTRAINT inspections_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE SET NULL;


--
-- Name: vehicles vehicles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

