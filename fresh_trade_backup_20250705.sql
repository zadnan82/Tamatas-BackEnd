--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-1.pgdg120+1)
-- Dumped by pg_dump version 15.13 (Debian 15.13-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: contactpreference; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.contactpreference AS ENUM (
    'messages_only',
    'whatsapp_only',
    'both'
);


ALTER TYPE public.contactpreference OWNER TO postgres;

--
-- Name: forumcategory; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.forumcategory AS ENUM (
    'gardening_tips',
    'trading_ideas',
    'general_discussion',
    'site_feedback'
);


ALTER TYPE public.forumcategory OWNER TO postgres;

--
-- Name: listingstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.listingstatus AS ENUM (
    'active',
    'pending',
    'completed',
    'expired'
);


ALTER TYPE public.listingstatus OWNER TO postgres;

--
-- Name: listingtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.listingtype AS ENUM (
    'for_sale',
    'looking_for'
);


ALTER TYPE public.listingtype OWNER TO postgres;

--
-- Name: messagetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.messagetype AS ENUM (
    'inquiry',
    'offer',
    'general'
);


ALTER TYPE public.messagetype OWNER TO postgres;

--
-- Name: priceunit; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.priceunit AS ENUM (
    'per_lb',
    'per_kg',
    'per_piece',
    'per_dozen',
    'per_bag'
);


ALTER TYPE public.priceunit OWNER TO postgres;

--
-- Name: tradepreference; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.tradepreference AS ENUM (
    'sale_only',
    'trade_only',
    'both'
);


ALTER TYPE public.tradepreference OWNER TO postgres;

--
-- Name: tradetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.tradetype AS ENUM (
    'sale',
    'trade',
    'purchase'
);


ALTER TYPE public.tradetype OWNER TO postgres;

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
-- Name: favorites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.favorites (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    listing_id character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.favorites OWNER TO postgres;

--
-- Name: forum_post_likes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_post_likes (
    id character varying NOT NULL,
    post_id character varying NOT NULL,
    user_id character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.forum_post_likes OWNER TO postgres;

--
-- Name: forum_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_posts (
    id character varying NOT NULL,
    topic_id character varying NOT NULL,
    content text NOT NULL,
    parent_post_id character varying,
    created_by character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now(),
    updated_date timestamp with time zone
);


ALTER TABLE public.forum_posts OWNER TO postgres;

--
-- Name: forum_topic_likes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_topic_likes (
    id character varying NOT NULL,
    topic_id character varying NOT NULL,
    user_id character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.forum_topic_likes OWNER TO postgres;

--
-- Name: forum_topics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forum_topics (
    id character varying NOT NULL,
    title character varying NOT NULL,
    content text NOT NULL,
    category public.forumcategory NOT NULL,
    is_pinned boolean,
    is_locked boolean,
    view_count integer,
    created_by character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now(),
    updated_date timestamp with time zone
);


ALTER TABLE public.forum_topics OWNER TO postgres;

--
-- Name: listings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.listings (
    id character varying NOT NULL,
    title character varying NOT NULL,
    description text,
    category character varying NOT NULL,
    subcategory character varying,
    listing_type public.listingtype NOT NULL,
    price double precision,
    price_unit public.priceunit,
    quantity_available character varying,
    trade_preference public.tradepreference,
    images json,
    status public.listingstatus,
    harvest_date timestamp without time zone,
    organic boolean,
    location json NOT NULL,
    view_count integer,
    created_by character varying NOT NULL,
    created_date timestamp with time zone DEFAULT now(),
    updated_date timestamp with time zone
);


ALTER TABLE public.listings OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    id character varying NOT NULL,
    sender_id character varying NOT NULL,
    recipient_id character varying NOT NULL,
    listing_id character varying,
    content text NOT NULL,
    read boolean,
    message_type public.messagetype,
    created_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: reviews; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reviews (
    id character varying NOT NULL,
    reviewer_id character varying NOT NULL,
    reviewed_user_id character varying NOT NULL,
    listing_id character varying,
    rating integer NOT NULL,
    comment text,
    trade_type public.tradetype,
    product_quality integer,
    communication integer,
    delivery integer,
    created_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.reviews OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    email character varying NOT NULL,
    full_name character varying,
    hashed_password character varying NOT NULL,
    bio text,
    phone character varying,
    address character varying,
    profile_image character varying,
    is_active boolean,
    created_date timestamp with time zone DEFAULT now(),
    updated_date timestamp with time zone,
    location json,
    latitude double precision,
    longitude double precision,
    location_precision character varying,
    search_radius integer,
    whatsapp_number character varying,
    contact_preference public.contactpreference,
    show_whatsapp_on_listings boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
abfbf3ef5223
\.


--
-- Data for Name: favorites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.favorites (id, user_id, listing_id, created_date) FROM stdin;
73f795a0-ce4f-42a4-a60a-12f4f44eae45	94c45427-a54c-47cf-a57d-6c808c9d2d62	84f38eee-d410-49ba-83ae-9d9f2056bb05	2025-07-05 15:01:02.2831+00
\.


--
-- Data for Name: forum_post_likes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forum_post_likes (id, post_id, user_id, created_date) FROM stdin;
\.


--
-- Data for Name: forum_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forum_posts (id, topic_id, content, parent_post_id, created_by, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: forum_topic_likes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forum_topic_likes (id, topic_id, user_id, created_date) FROM stdin;
\.


--
-- Data for Name: forum_topics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forum_topics (id, title, content, category, is_pinned, is_locked, view_count, created_by, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: listings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.listings (id, title, description, category, subcategory, listing_type, price, price_unit, quantity_available, trade_preference, images, status, harvest_date, organic, location, view_count, created_by, created_date, updated_date) FROM stdin;
66fbc049-ccc1-4613-aff1-13df0cfd9b59	Looking for Fresh Strawberries	Restaurant looking for 10+ lbs of fresh strawberries for our dessert menu.	berries	\N	looking_for	\N	per_lb	10+ lbs needed	sale_only	\N	active	\N	f	{"city": "Chicago", "state": "IL", "latitude": 41.8781, "longitude": -87.6298}	1	9c2a3cf1-e200-4ba0-a7ff-68e7788d73ca	2025-07-04 22:13:23.081335+00	2025-07-05 09:33:37.713743+00
84f38eee-d410-49ba-83ae-9d9f2056bb05	Apples	Fresh apples 	apples_pears	\N	for_sale	10	per_kg	10	sale_only	["https://res.cloudinary.com/dr2knxtuq/image/upload/v1751706539/tamatas/listings/tamatas/listings/img_280_1751706539056.jpg"]	active	2025-07-04 00:00:00	t	{"city": "Stockholm", "state": "Farsta", "latitude": 59.243353, "longitude": 18.0939285}	16	f107161f-9ef6-4057-95fa-8b6a8ac76259	2025-07-05 09:09:40.223807+00	2025-07-05 15:05:57.96981+00
a1a7ffae-f877-4594-95d5-ef171e44dad2	Fresh Organic Tomatoes	Vine-ripened heirloom tomatoes from our organic farm. Perfect for salads and cooking.	tomatoes_peppers	\N	for_sale	4.5	per_lb	20 lbs available	both	["https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500"]	active	\N	t	{"city": "Springfield", "state": "IL", "latitude": 39.7817, "longitude": -89.6501}	2	60622852-3d2d-45bd-b294-b38f2de3bbee	2025-07-04 22:13:23.081335+00	2025-07-05 15:06:10.279029+00
484aa78c-7d9f-4c61-ac2e-75227306cfc6	Fresh Basil Leaves	Aromatic sweet basil, perfect for pesto and Italian cooking.	herbs	\N	for_sale	3	per_bag	10 bags available	both	["https://images.unsplash.com/photo-1618375569909-3c8616cf5ecf?w=500"]	active	\N	t	{"city": "Madison", "state": "WI", "latitude": 43.0731, "longitude": -89.4012}	1	c7da635b-cb84-4ff4-b3e3-e78435530ad1	2025-07-04 22:13:23.081335+00	2025-07-05 15:19:56.253091+00
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.messages (id, sender_id, recipient_id, listing_id, content, read, message_type, created_date) FROM stdin;
6db1d5fe-b343-4a96-a7c5-fad02d901b90	94c45427-a54c-47cf-a57d-6c808c9d2d62	f107161f-9ef6-4057-95fa-8b6a8ac76259	\N	hej	f	general	2025-07-05 15:00:37.682155+00
\.


--
-- Data for Name: reviews; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reviews (id, reviewer_id, reviewed_user_id, listing_id, rating, comment, trade_type, product_quality, communication, delivery, created_date) FROM stdin;
e41ebc44-b179-4aa0-940d-853932fcf595	94c45427-a54c-47cf-a57d-6c808c9d2d62	c7da635b-cb84-4ff4-b3e3-e78435530ad1	\N	5	good farmer	\N	\N	\N	\N	2025-07-05 15:28:16.568115+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, full_name, hashed_password, bio, phone, address, profile_image, is_active, created_date, updated_date, location, latitude, longitude, location_precision, search_radius, whatsapp_number, contact_preference, show_whatsapp_on_listings) FROM stdin;
c7da635b-cb84-4ff4-b3e3-e78435530ad1	gardener@example.com	Jane Gardener	$2b$12$.pj56IFOpmmQfDUm9KPUJ.N7/jnNhVx24C9YE.YjVaa0nCg/azA52	Home gardener passionate about fresh vegetables	+1-555-0102	456 Garden Lane, Madison, WI	\N	t	2025-07-04 22:13:21.938077+00	\N	\N	\N	\N	city	25	\N	both	f
9c2a3cf1-e200-4ba0-a7ff-68e7788d73ca	chef@example.com	Chef Mike	$2b$12$R5b5busnL9pWufwO3rLM4uqnxqj02ZXUh4vAwkdMGmdjzJ0do4IQe	Restaurant chef looking for fresh local ingredients	+1-555-0103	789 Culinary St, Chicago, IL	\N	t	2025-07-04 22:13:21.938077+00	\N	\N	\N	\N	city	25	\N	both	f
01858e34-8322-4146-ba32-d38ffc0be933	testuser@example.com	Test User	$2b$12$WtawgKQn1H2pMNYpsinImeGRK7p8Z.s1KMIBPB40/dKk/dgdCrXae	Testing the new location system	\N	\N	\N	t	2025-07-04 22:20:06.193086+00	\N	{"country": "United States", "city": "San Francisco", "state": "California", "latitude": 37.7792588, "longitude": -122.4193286, "formatted_address": "San Francisco, California, United States"}	37.7792588	-122.4193286	city	30	+1-555-9999	both	f
60622852-3d2d-45bd-b294-b38f2de3bbee	farmer@example.com	John Farmer	$2b$12$ORvfkKsENoAayrtY2Gwq0.RSWMC0aq/JdNhzN2M9bLQ.dkZTPUxCa	Organic farmer with 10+ years experience	+1-555-0101	123 Farm Road, Springfield, IL	\N	t	2025-07-04 22:13:21.938077+00	2025-07-04 22:25:41.276371+00	{"country": "United States", "city": "Springfield", "state": "Illinois", "area": null, "formatted_address": "Springfield, Sangamon County, Illinois, United States"}	39.7990175	-89.6439575	city	25	\N	both	f
b32c945c-551d-4b98-8cd9-9478c2ea3339	zoro@hotmail.com	Zoro 	$2b$12$x2iJLOjpkbyEVF18Nmcbk.itUpuPt/sm7ae0UQksXBFgidh5THU62					t	2025-07-05 08:30:11.1459+00	\N	{"country": "Sweden", "city": "Stockholm", "state": "Farsta", "area": "Farsta", "latitude": 59.243353, "longitude": 18.0939285, "formatted_address": "Farsta, Kroppaplan, Farsta, Farsta stadsdelsomr\\u00e5de, Stockholm, Stockholm Municipality, Stockholm County, 123 41, Sweden"}	59.243353	18.0939285	city	25		both	f
f107161f-9ef6-4057-95fa-8b6a8ac76259	ggg@ggg.com	Gina	$2b$12$pzTavfd80eehmgf/rfiK6e3VhBkTPiMKqJLc2tLqo0AUK/oxnTL7i					t	2025-07-05 08:35:17.962587+00	2025-07-05 08:41:56.618952+00	{"country": "Sweden", "city": "Stockholm", "state": "Farsta", "area": "Farsta"}	59.243353	18.0939285	neighborhood	25	+46736953102	both	t
94c45427-a54c-47cf-a57d-6c808c9d2d62	zainabadnan@hotmail.com	Zainab Adnan	$2b$12$xl/0hvrNBTLD4tXW09RGJO.jFY6qUBP8SaU1xdMq..wTNK9kaCRCG					t	2025-07-05 09:51:24.873313+00	\N	{"country": "Sweden", "city": "Stockholm", "state": "Farsta", "area": "Farsta", "latitude": 59.243353, "longitude": 18.0939285, "formatted_address": "Farsta, Kroppaplan, Farsta, Farsta stadsdelsomr\\u00e5de, Stockholm, Stockholm Municipality, Stockholm County, 123 41, Sweden"}	59.243353	18.0939285	city	25		both	f
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (id);


--
-- Name: forum_post_likes forum_post_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_post_likes
    ADD CONSTRAINT forum_post_likes_pkey PRIMARY KEY (id);


--
-- Name: forum_posts forum_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_posts
    ADD CONSTRAINT forum_posts_pkey PRIMARY KEY (id);


--
-- Name: forum_topic_likes forum_topic_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_topic_likes
    ADD CONSTRAINT forum_topic_likes_pkey PRIMARY KEY (id);


--
-- Name: forum_topics forum_topics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_topics
    ADD CONSTRAINT forum_topics_pkey PRIMARY KEY (id);


--
-- Name: listings listings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.listings
    ADD CONSTRAINT listings_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_favorites_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_favorites_id ON public.favorites USING btree (id);


--
-- Name: ix_forum_post_likes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forum_post_likes_id ON public.forum_post_likes USING btree (id);


--
-- Name: ix_forum_posts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forum_posts_id ON public.forum_posts USING btree (id);


--
-- Name: ix_forum_topic_likes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forum_topic_likes_id ON public.forum_topic_likes USING btree (id);


--
-- Name: ix_forum_topics_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forum_topics_id ON public.forum_topics USING btree (id);


--
-- Name: ix_listings_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_listings_id ON public.listings USING btree (id);


--
-- Name: ix_messages_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_messages_id ON public.messages USING btree (id);


--
-- Name: ix_post_user_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_post_user_like ON public.forum_post_likes USING btree (post_id, user_id);


--
-- Name: ix_reviews_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reviews_id ON public.reviews USING btree (id);


--
-- Name: ix_topic_user_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_topic_user_like ON public.forum_topic_likes USING btree (topic_id, user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: favorites favorites_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: favorites favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: forum_post_likes forum_post_likes_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_post_likes
    ADD CONSTRAINT forum_post_likes_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.forum_posts(id);


--
-- Name: forum_post_likes forum_post_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_post_likes
    ADD CONSTRAINT forum_post_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: forum_posts forum_posts_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_posts
    ADD CONSTRAINT forum_posts_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: forum_posts forum_posts_parent_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_posts
    ADD CONSTRAINT forum_posts_parent_post_id_fkey FOREIGN KEY (parent_post_id) REFERENCES public.forum_posts(id);


--
-- Name: forum_posts forum_posts_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_posts
    ADD CONSTRAINT forum_posts_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.forum_topics(id);


--
-- Name: forum_topic_likes forum_topic_likes_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_topic_likes
    ADD CONSTRAINT forum_topic_likes_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.forum_topics(id);


--
-- Name: forum_topic_likes forum_topic_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_topic_likes
    ADD CONSTRAINT forum_topic_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: forum_topics forum_topics_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forum_topics
    ADD CONSTRAINT forum_topics_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: listings listings_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.listings
    ADD CONSTRAINT listings_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: messages messages_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: messages messages_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: reviews reviews_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: reviews reviews_reviewed_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_reviewed_user_id_fkey FOREIGN KEY (reviewed_user_id) REFERENCES public.users(id);


--
-- Name: reviews reviews_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

