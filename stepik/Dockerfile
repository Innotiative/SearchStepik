FROM nginx:alpine AS production

WORKDIR /app

COPY index.html /usr/share/nginx/html
COPY settings.html /usr/share/nginx/html

COPY asset /usr/share/nginx/html/asset
COPY asset /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN ln -s /usr/share/nginx/html /usr/share/nginx/html/catalog

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
